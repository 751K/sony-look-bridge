"""Numerical checks for Log encoding, gamut conversion, highlights and cube layout."""
import tempfile
import unittest
from pathlib import Path

import numpy as np

import video_color as V
import video_look as L


class VideoColorTests(unittest.TestCase):
    def test_slog3_code_values(self):
        # Sony appendix: black 95, 18% grey 420, 90% white rounds to 598.
        actual = V.slog3_encode([0, 0.18, 0.9]) * 1023
        np.testing.assert_allclose(actual[:2], [95, 420], atol=1e-12)
        self.assertEqual(round(actual[2]), 598)
        np.testing.assert_allclose(V.slog3_decode(np.array([95, 420]) / 1023), [0, 0.18], atol=1e-14)

    def test_log_roundtrip_across_toe_and_highlights(self):
        scene = np.r_[-0.01, -0.001, 0, 0.01125, np.geomspace(1e-8, 38, 3000)]
        np.testing.assert_allclose(V.slog3_decode(V.slog3_encode(scene)), scene, atol=1e-12)
        toe = V.slog3_encode([0.01125 - 1e-10, 0.01125 + 1e-10])
        self.assertLess(abs(toe[1] - toe[0]), 1e-8)

    def test_matrices_match_sony_appendix(self):
        reference = {
            "SGamut3": [[0.7064827132, 0.1288010498, 0.1151721641],
                        [0.2709796708, 0.7866064112, -0.0575860820],
                        [-0.0096778454, 0.0046000375, 1.0941355587]],
            "SGamut3Cine": [[0.5990839208, 0.2489255161, 0.1024464902],
                            [0.2150758201, 0.8850685017, -0.1001443219],
                            [-0.0320658495, -0.0276583907, 1.1487819910]],
        }
        for name, matrix in reference.items():
            np.testing.assert_allclose(V.RGB_TO_XYZ[name], matrix, atol=6e-11, rtol=0)

    def test_aces_white_and_direct_conversion_equivalence(self):
        for name, matrix in V.RGB_TO_XYZ.items():
            np.testing.assert_allclose(V.GAMUT_TO_ACES[name] @ np.ones(3), np.ones(3), atol=1e-14)
            # Going through ACES must agree with direct D65 gamut conversion.
            np.testing.assert_allclose(V.ACES_TO_SRGB @ V.GAMUT_TO_ACES[name],
                                       np.linalg.solve(V.SRGB_TO_XYZ, matrix), atol=1e-14)
        np.testing.assert_allclose(V.D65_TO_D60 @ V.WHITE_XYZ, V.AP0_WHITE_XYZ, atol=1e-14)

    def test_both_gamuts_represent_same_scene(self):
        xyz = np.array([[0.2, 0.3, 0.1], [0.05, 0.06, 0.07], V.WHITE_XYZ * 4])
        outputs = []
        for name, matrix in V.RGB_TO_XYZ.items():
            code = V.slog3_encode(xyz @ np.linalg.inv(matrix).T)
            outputs.append(V.log_to_aces(code, name))
        np.testing.assert_allclose(*outputs, atol=1e-14)

    def test_shoulder_monotonicity_continuity_and_colour_ratios(self):
        levels = np.linspace(0, 40, 10001)
        camera = levels[:, None] * np.array([1, 0.4, 0.1])
        result = V.highlight_shoulder(camera, 0.9, 2.3)
        np.testing.assert_allclose(result[levels <= 0.9], camera[levels <= 0.9])
        self.assertTrue((np.diff(result, axis=0) >= 0).all())
        self.assertLess(result[-1, 0], 2.3)
        np.testing.assert_allclose(result[1:, 1] / result[1:, 0], 0.4)
        np.testing.assert_allclose(result[1:, 2] / result[1:, 0], 0.1)
        h = 1e-6
        p = np.repeat(np.array([0.9 - h, 0.9, 0.9 + h])[:, None], 3, axis=1)
        out = V.highlight_shoulder(p, 0.9, 2.3)[:, 0]
        np.testing.assert_allclose(np.diff(out) / h, 1, atol=1e-6)

    def test_display_transfer_preserves_light(self):
        s = np.linspace(0, 1, 1000)
        expected = np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)
        np.testing.assert_allclose(V.srgb_to_gamma24(s) ** 2.4, expected, atol=1e-15)

    def test_extreme_codes_are_finite(self):
        axis = np.linspace(0, 1, 11)
        grid = np.stack(np.meshgrid(axis, axis, axis, indexing="ij"), axis=-1)
        for gamut in V.PRIMARIES:
            rgb = V.positive_rgb(V.log_to_aces(grid, gamut) @ V.ACES_TO_SRGB.T)
            out = V.highlight_shoulder(rgb, 0.9, 2.3)
            self.assertTrue(np.isfinite(out).all())
            self.assertGreaterEqual(out.min(), 0)
            self.assertLess(out.max(), 2.3)

    def test_cube_red_fastest_layout_and_tetrahedral_interpolation(self):
        axis = np.linspace(0, 1, 5)
        table = np.stack(np.meshgrid(axis, axis, axis, indexing="ij"), axis=-1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "identity.cube"
            L.write_cube(path, table, "Identity")
            lines = path.read_text().splitlines()
            rows = np.array([[float(x) for x in line.split()] for line in lines
                             if line and line[0].isdigit()])
            np.testing.assert_equal(rows[1], [0.25, 0, 0])
            np.testing.assert_equal(rows[5], [0, 0.25, 0])
            np.testing.assert_equal(rows[25], [0, 0, 0.25])
            loaded = rows.reshape(5, 5, 5, 3).transpose(2, 1, 0, 3)
            code = np.random.default_rng(2).uniform(0, 1, (1000, 3))
            np.testing.assert_allclose(V.tetrahedral(loaded, code), code, atol=1e-15)

    def test_negative_gamut_mapping_preserves_luminance(self):
        x = np.array([[-.2, .5, 1.], [1., -.1, .8], [.2, .3, .4], [0., 0., 0.]])
        out = V.positive_rgb(x)
        self.assertGreaterEqual(out.min(), 0)
        np.testing.assert_allclose(out @ V.SRGB_TO_XYZ[1], x @ V.SRGB_TO_XYZ[1], atol=1e-14)
        np.testing.assert_allclose(out[2:], x[2:], atol=1e-15)


class SensorCalibrationTests(unittest.TestCase):
    def synthetic_capture(self, matrix, scale, size=(1080, 1920)):
        """Render the chart into an image with a perspective warp; returns (photo, video)."""
        import sensor_calibration as C
        h_img, w_img = size
        corners = np.array([[180, 120], [1750, 160], [150, 980], [1780, 940]], float)
        h = C.homography(corners, C.MARKERS)          # image -> chart
        yy, xx = np.mgrid[0:h_img, 0:w_img]
        chart = C.apply_h(h, np.c_[xx.ravel(), yy.ravel()]).reshape(h_img, w_img, 2)
        video = np.full((h_img, w_img, 3), 0.004)
        for col, row, rgb in C.patches():
            cx, cy = C.patch_centre(col, row)
            inside = ((np.abs(chart[..., 0] - cx) < C.PITCH[0] * .4)
                      & (np.abs(chart[..., 1] - cy) < C.PITCH[1] * .4))
            video[inside] = (np.asarray(rgb) ** 2.2) * 0.5   # some linear scene value
        for mx, my in C.MARKERS:
            inside = ((np.abs(chart[..., 0] - mx) < 35) & (np.abs(chart[..., 1] - my) < 35))
            video[inside] = 1.0
        photo = np.clip(video @ matrix.T * scale, 0, None)
        return photo, video

    def test_recovers_known_matrix_through_detection(self):
        import sensor_calibration as C
        truth = np.array([[1.5, -0.3, -0.2], [-0.2, 1.4, -0.2], [-0.1, -0.3, 1.4]])
        wb_truth = np.array([0.93, 1.0, 1.07])
        photo, video = self.synthetic_capture(np.diag(wb_truth) @ truth, 0.37)
        p = C.sample_patches(photo, C.find_markers(photo))
        v = C.sample_patches(video, C.find_markers(video))
        use = p.min(1) > 1e-4
        m, s, wb = C.fit_matrix(v[use], p[use], 1 / p[use].sum(1))
        np.testing.assert_allclose(m, truth, atol=1e-6)
        np.testing.assert_allclose(s * wb, 0.37 * wb_truth, atol=1e-6)
        np.testing.assert_allclose(m @ np.ones(3), np.ones(3), atol=1e-12)

    def test_chart_layout_fits_canvas(self):
        import sensor_calibration as C
        self.assertEqual(len(C.patches()), C.COLS * C.ROWS)
        for col, row, rgb in C.patches():
            cx, cy = C.patch_centre(col, row)
            self.assertTrue(0 < cx < C.CANVAS[0] and 0 < cy < C.CANVAS[1])
            self.assertLessEqual(max(rgb), 0.8 + 1e-12)   # stays below the white markers
        self.assertIn("display-p3", C.chart_html())

    def test_sensor_bridge_maps_aces_to_camera(self):
        import json as _json
        matrix = np.array([[1.2, -0.1, -0.1], [-0.05, 1.1, -0.05], [0., -0.2, 1.2]])
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "m.json"
            path.write_text(_json.dumps({"gamut": "SGamut3Cine", "matrix": matrix.tolist()}))
            bridge = L.SensorBridge(path)
        lin = np.array([[0.1, 0.2, 0.3], [0.18, 0.18, 0.18]])
        for gamut in ("SGamut3", "SGamut3Cine"):
            code = V.slog3_encode(lin @ np.linalg.solve(V.RGB_TO_XYZ[gamut], V.RGB_TO_XYZ["SGamut3Cine"]).T)
            np.testing.assert_allclose(bridge.camera_from_aces(V.log_to_aces(code, gamut)),
                                       lin @ matrix.T, atol=1e-12)


if __name__ == "__main__":
    unittest.main()
