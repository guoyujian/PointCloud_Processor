
from loguru import logger
import os.path as osp
import open3d as o3d


def compute_convex_hull_and_its_volume(pcd_filepath: str):
    dir_path = osp.dirname(pcd_filepath)
    base_filename = osp.basename(pcd_filepath).replace('.pcd', '')

    pcd: o3d.geometry.PointCloud = o3d.io.read_point_cloud(pcd_filepath)
    down_sample_voxel = 0.3

    pcd = pcd.voxel_down_sample(down_sample_voxel)
    logger.info(f'体素降采样{down_sample_voxel}')
    # pcd.compute_mean_and_covariance()
    hull,  _ = pcd.compute_convex_hull()
    hull: o3d.geometry.TriangleMesh
    volume = hull.get_volume()
    hull_ls = o3d.geometry.LineSet.create_from_triangle_mesh(hull)
    hull_ls.paint_uniform_color((1, 0, 0))
    vis = o3d.visualization.Visualizer()
    vis.create_window()
    vis.add_geometry(pcd)
    vis.add_geometry(hull_ls)
    vis.run()
    screenshot_filepath = osp.join(dir_path, f'{base_filename}_convex_hull_volume_{volume}_{down_sample_voxel}.jpg')
    vis.capture_screen_image(screenshot_filepath)
    vis.destroy_window()
    # logger.info(f'凸包体积为：{volume}')
    return screenshot_filepath, volume


def main():
    print('脚本生成点云凸包截图并计算凸包体积\n注：程序将在pcd文件同级目录下生成结果')
    while True:
        s = input('\n请输入待处理的文件路径，输入‘exit’结束程序：')
        if s.lower() == 'exit':
            break
        # 解析文件夹路径

        screenshot_filepath, volume = compute_convex_hull_and_its_volume(s)
        print(f'凸包屏幕截图：{screenshot_filepath}')
        print(f'{s} 点云的凸包体积：{volume} 立方米')


if __name__ == '__main__':
    main()