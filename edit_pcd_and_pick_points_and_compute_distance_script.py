from typing import List

from loguru import logger
import os.path as osp
import open3d as o3d
import random
from collections import namedtuple
from conf.pc_conf import SPHERE_RADIUS
from math import sqrt
from datetime import datetime

Color = namedtuple('Color', 'name, rgb_array')
COLORS = [
    Color(name='赤', rgb_array=[1., 0., 0.]),
    Color(name='橙', rgb_array=[1., 0.647, 0.]),
    Color(name='黄', rgb_array=[1., 1., 0.]),
    Color(name='绿', rgb_array=[0., 1., 0.]),
    Color(name='青', rgb_array=[0., 0.498, 1.]),
    Color(name='蓝', rgb_array=[0., 0., 1.]),
    Color(name='紫', rgb_array=[0.545, 0., 1.]),
]
Sphere = namedtuple('Sphere', 'color, center, pcd')


def get_cropped_pcd_and_picked_points_index_with_editing(pcd_filepath):
    if not osp.exists(pcd_filepath):
        # print('文件不存在，请检查')
        raise FileNotFoundError('文件不存在，请检查')
    if pcd_filepath[-3:] != 'pcd':
        raise RuntimeError('文件扩展名非pcd，请检查')

    pcd: o3d.geometry.PointCloud = o3d.io.read_point_cloud(pcd_filepath)
    vis = o3d.visualization.VisualizerWithEditing()
    vis.create_window()
    vis.add_geometry(pcd)

    vis.run()  # user edit and picks points
    vis.destroy_window()
    picked_points_index = vis.get_picked_points()
    cropped_pcd = vis.get_cropped_geometry()
    # vis.close()
    return cropped_pcd, picked_points_index


def compute_distance(p1_xyz, p2_xyz):
    '''
    计算两点欧式距离
    :param p1_xyz:
    :param p2_xyz:
    :return:
    '''
    d = 0
    for p1_coordinate, p2_coordinate in zip(p1_xyz, p2_xyz):
        d += pow(p1_coordinate - p2_coordinate, 2)
    d = sqrt(d)
    return d


def save_cropped_pcd_and_screenshot_and_distance_result(pcd, pick_points_indexes, dir_path, base_filename):
    t = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    save_cropped_pcd_filepath = osp.join(dir_path, f'{base_filename}_cropped_{t}.pcd')
    save_screenshot_filepath = osp.join(dir_path, f'{base_filename}_screenshot_{t}.jpg')
    save_distance_filepath = osp.join(dir_path, f'{base_filename}_distance_res_{t}.txt')

    o3d.io.write_point_cloud(save_cropped_pcd_filepath, pcd)
    vis = o3d.visualization.VisualizerWithKeyCallback()
    vis.create_window()
    vis.add_geometry(pcd)
    # pcd_list = [pcd]
    # 将球的颜色和球心坐标记录下来
    spheres: List[Sphere] = []

    # spheres_color_and_coor = []
    # spheres = [] # 球点云列表
    r = SPHERE_RADIUS
    select_colors_index = random.sample(range(len(COLORS)), len(pick_points_indexes))
    for point_index, color_index in zip(pick_points_indexes, select_colors_index):
        xyz = pcd.points[point_index]
        # 以选择的点为球心画一个球
        sphere: o3d.geometry.TriangleMesh = o3d.geometry.TriangleMesh.create_sphere(r)
        sphere.compute_vertex_normals()
        sphere.translate(xyz)
        sphere.paint_uniform_color(COLORS[color_index].rgb_array)

        logger.info(f'{COLORS[color_index].name}色点的坐标为：{xyz}')
        spheres.append(Sphere(COLORS[color_index], xyz, sphere))
        vis.add_geometry(sphere)

    def smaller_point(vis: o3d.visualization.Visualizer, action, mods):
        nonlocal r, spheres
        if action == 1:  # key down
            spheres_new = []
            r = r - 0.02 if r - 0.02 > 0 else 0.01
            for s in spheres:
                point_color_obj, center = s.color, s.center
                sphere_new = o3d.geometry.TriangleMesh.create_sphere(r)
                sphere_new.compute_vertex_normals()
                sphere_new.translate(center)
                sphere_new.paint_uniform_color(point_color_obj.rgb_array)
                spheres_new.append(Sphere(
                    point_color_obj,
                    center,
                    sphere_new
                ))
                vis.remove_geometry(s.pcd)
                vis.add_geometry(sphere_new)
            spheres = spheres_new

            return False

        return False

    def bigger_point(vis: o3d.visualization.Visualizer, action, mods):
        nonlocal r, spheres
        if action == 1:  # key down
            spheres_new = []
            r = r + 0.02
            for s in spheres:
                point_color_obj, center = s.color, s.center
                sphere_new = o3d.geometry.TriangleMesh.create_sphere(r)
                sphere_new.compute_vertex_normals()
                sphere_new.translate(center)
                sphere_new.paint_uniform_color(point_color_obj.rgb_array)
                spheres_new.append(Sphere(
                    point_color_obj,
                    center,
                    sphere_new
                ))
                vis.remove_geometry(s.pcd)
                vis.add_geometry(sphere_new)
            spheres = spheres_new

            return False

        return False

    vis.register_key_action_callback(ord('.'), bigger_point)
    vis.register_key_action_callback(ord(','), smaller_point)
    # vis.register_key_action_callback(80, smaller_point)

    vis.run()
    vis.capture_screen_image(save_screenshot_filepath)
    vis.destroy_window()
    # save
    with open(save_distance_filepath, 'w') as f:
        f.write('点1（颜色）\t点1坐标\t点2（颜色）\t点2坐标\t距离（m）\n')
        for i, sphere1 in enumerate(spheres):
            for sphere2 in spheres[i+1:]:
                distance = compute_distance(sphere1.center, sphere2.center)
                logger.info(f'{sphere1[0]}色点和{sphere2[0]}色点的距离为 {distance} m')
                f.write(f'{sphere1.color.name}\t{sphere1.center}\t{sphere2.color.name}\t{sphere2.center}\t{distance}\n')
    return save_cropped_pcd_filepath, save_screenshot_filepath, save_distance_filepath


def main():
    print('注：程序将在pcd文件同级目录下生成结果')
    while True:
        s = input('\n请输入待处理的文件路径，输入‘exit’结束程序：')
        if s.lower() == 'exit':
            break
        # 解析文件夹路径
        dir_path = osp.dirname(s)
        base_filename = osp.basename(s).replace('.pcd', '')
        try:
            print('edit and pick points...')
            cropped_pcd, picked_points_indexes = get_cropped_pcd_and_picked_points_index_with_editing(s)
        except (FileNotFoundError, RuntimeError) as e:
            print(e)
            continue
        if len(picked_points_indexes) == 0:
            print('未选择任何点')
        # 打开新的视窗，让用户调整视角，在用户关闭窗口时保存当前截图
        # 计算点的坐标生成txt结果文件
        cmd = input('- 输入任意键打开处理后的点云和选择的点，调整视角，关闭窗口将自动保存截图并计算点点的欧式距离\n'
                    '- 输入exit，放弃本次编辑：')
        if cmd == 'exit':
            print(f'放弃本次编辑')
            continue
        save_cropped_pcd_filepath, save_screenshot_filepath, save_distance_filepath = \
            save_cropped_pcd_and_screenshot_and_distance_result(cropped_pcd,
                                                                picked_points_indexes,
                                                                dir_path,
                                                                base_filename)
        print(f'保存裁剪后的点云文件路径：{save_cropped_pcd_filepath}')
        print(f'保存屏幕截图：{save_screenshot_filepath}')
        print(f'保存计算距离结果：{save_distance_filepath}')


if __name__ == '__main__':
    main()