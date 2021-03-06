import unittest

from pathlib import Path

try:
    from unittest.mock import call, patch
except ImportError:
    # Python 2
    from mock import call, patch

import numpy as np

from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None

from pylibdmtx.pylibdmtx import (
    decode, Decoded, Rect, PyLibDMTXError, EXTERNAL_DEPENDENCIES
)


TESTDATA = Path(__file__).parent


class TestDecode(unittest.TestCase):
    EXPECTED = [
        Decoded(
            data=b'Stegosaurus',
            rect=Rect(left=5, top=6, width=96, height=95)
        ),
        Decoded(
            data=b'Plesiosaurus',
            rect=Rect(left=298, top=6, width=95, height=95)
        )
    ]

    def setUp(self):
        self.datamatrix = Image.open(str(TESTDATA.joinpath('datamatrix.png')))
        self.empty = Image.open(str(TESTDATA.joinpath('empty.png')))

    def tearDown(self):
        self.datamatrix = self.empty = None

    def test_decode(self):
        "Read both barcodes in `datamatrix.png`"
        res = decode(self.datamatrix)
        self.assertEqual(self.EXPECTED, res)

    def test_decode_single(self):
        "Read just one of the barcodes in `datamatrix.png`"
        res = decode(self.datamatrix, max_count=1)
        self.assertEqual(self.EXPECTED[:1], res)

    def test_decode_tuple(self):
        "Read barcodes in pixels"
        pixels = self.datamatrix.copy().convert('RGB').tobytes()
        width, height = self.datamatrix.size[:2]
        res = decode((pixels, width, height))
        self.assertEqual(self.EXPECTED, res)

    def test_empty(self):
        "Do not show any output for an image that does not contain a barcode"
        res = decode(self.empty)
        self.assertEqual([], res)

    def test_decode_numpy(self):
        "Read image using Pillow and convert to numpy.ndarray"
        res = decode(np.asarray(self.datamatrix))
        self.assertEqual(self.EXPECTED, res)

    @unittest.skipIf(cv2 is None, 'OpenCV not installed')
    def test_decode_opencv(self):
        "Read image using OpenCV"
        res = decode(cv2.imread(str(TESTDATA.joinpath('datamatrix.png'))))
        self.assertEqual(self.EXPECTED, res)

    def test_external_dependencies(self):
        "External dependencies"
        self.assertEqual(1, len(EXTERNAL_DEPENDENCIES))
        self.assertIn('libdmtx', EXTERNAL_DEPENDENCIES[0]._name)

    @patch('pylibdmtx.pylibdmtx.dmtxImageCreate')
    def test_dmtxImageCreate_failed(self, dmtxImageCreate):
        dmtxImageCreate.return_value = None
        self.assertRaisesRegexp(
            PyLibDMTXError, 'Could not create image', decode, self.datamatrix
        )
        self.assertEqual(1, dmtxImageCreate.call_count)

    @patch('pylibdmtx.pylibdmtx.dmtxDecodeCreate')
    def test_dmtxDecodeCreate_failed(self, dmtxDecodeCreate):
        dmtxDecodeCreate.return_value = None
        self.assertRaisesRegexp(
            PyLibDMTXError, 'Could not create decoder', decode, self.datamatrix
        )
        self.assertEqual(1, dmtxDecodeCreate.call_count)

    def test_unsupported_bits_per_pixel(self):
        # 40 bits-per-pixel
        data = (list(range(3 * 3 * 5)), 3, 3)
        self.assertRaisesRegexp(
            PyLibDMTXError,
            (
                'Unsupported bits-per-pixel: \[40\] Should be one of '
                '\[8, 16, 24, 32\]'
            ),
            decode, data
        )

    def test_inconsistent_dimensions(self):
        # Image data has ten bytes. width x height indicates nine bytes
        data = (list(range(10)), 3, 3)
        self.assertRaisesRegexp(
            PyLibDMTXError,
            (
                'Inconsistent dimensions: image data of 10 bytes is not '
                'divisible by \(width x height = 9\)'
            ),
            decode, data
        )


if __name__ == '__main__':
    unittest.main()
