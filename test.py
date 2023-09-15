import unittest
import os
from craw import create_directory
class TestCreateDirectory(unittest.TestCase):
    def test_create_directory(self):
        tag_name = '提高+_省选−_各省省选_湖南_2001'
        directory_name = '2222 [HNOI2001]_矩阵乘积'
        expected_result = 'data\\提高+_省选−_各省省选_湖南_2001\\2222 [HNOI2001]_矩阵乘积'
        
        directory_path = create_directory(tag_name, directory_name)
        
        self.assertEqual(directory_path, expected_result)
        self.assertTrue(os.path.exists(directory_path))
if __name__ == '__main__':
    unittest.main()
