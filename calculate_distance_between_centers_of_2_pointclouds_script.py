from loguru import logger
import os.path as osp
import open3d as o3d

from conf.pc_conf import SPHERE_RADIUS, MOVE_STEP
from edit_pcd_and_pick_points_and_compute_distance_script import compute_distance


def calculate_distance_between_centers_of_2_pointclouds_script(pcd_filepath1, pcd_filepath2):
    if not osp.exists(pcd_filepath1) or not osp.exists(pcd_filepath2):
        logger.error(f'文件不存在，请检查')
    pcd1: o3d.geometry.PointCloud = o3d.io.read_point_cloud(pcd_filepath1)
    pcd2: o3d.geometry.PointCloud = o3d.io.read_point_cloud(pcd_filepath2)
    center1 = pcd1.get_center()
    center2 = pcd2.get_center()
    center1 = [2.51459594e+00, 5.20916051e-01, 2.09759279e-03]
    center2 = [3.84690384e+00, - 6.58132727e+00, - 4.18279377e-03]


    # 将两个点云文件合并，标记质心并保存截图
    vis = o3d.visualization.VisualizerWithKeyCallback()
    vis.create_window()
    vis.add_geometry(pcd1)
    vis.add_geometry(pcd2)
    r = SPHERE_RADIUS
    sphere1: o3d.geometry.TriangleMesh = o3d.geometry.TriangleMesh.create_sphere(SPHERE_RADIUS)
    sphere1.compute_vertex_normals()
    sphere1.translate(center1)
    sphere1.paint_uniform_color([1., 0., 0.])
    sphere2: o3d.geometry.TriangleMesh = o3d.geometry.TriangleMesh.create_sphere(SPHERE_RADIUS)
    sphere2.compute_vertex_normals()
    sphere2.translate(center2)
    sphere2.paint_uniform_color([1., 0., 0.])

    vis.add_geometry(sphere1)
    vis.add_geometry(sphere2)

    activate_point = 1

    def activate_point1(vis1: o3d.visualization.Visualizer, action, mods):
        nonlocal activate_point
        if action == 1:
            logger.info(f'激活操作点1')
            activate_point = 1
        return False

    def activate_point2(vis1: o3d.visualization.Visualizer, action, mods):
        nonlocal activate_point
        if action == 1:
            logger.info(f'激活操作点2')
            activate_point = 2
        return False

    def move_up(vis1: o3d.visualization.Visualizer, action, mods):
        nonlocal sphere1, sphere2, center1, center2
        if action == 1:
            if activate_point == 1:
                center1[2] += MOVE_STEP
                logger.info(f'point1向上移动{MOVE_STEP}, 新坐标为：{center1}')
                sphere1.translate([0,0,MOVE_STEP])
                return True
            elif activate_point == 2:
                center2[2] += MOVE_STEP
                logger.info(f'point2向上移动{MOVE_STEP}, 新坐标为：{center2}')
                sphere2.translate([0, 0, MOVE_STEP])
                return True
        return False

    def move_down(vis1: o3d.visualization.Visualizer, action, mods):
        nonlocal sphere1, sphere2, center1, center2
        if action == 1:
            if activate_point == 1:
                center1[2] -= MOVE_STEP
                logger.info(f'point1向下移动{MOVE_STEP}, 新坐标为：{center1}')
                sphere1.translate([0, 0, -MOVE_STEP])
                return True
            elif activate_point == 2:
                center2[2] -= MOVE_STEP
                logger.info(f'point2向下移动{MOVE_STEP}, 新坐标为：{center2}')
                sphere2.translate([0, 0, -MOVE_STEP])
                return True
        return False


    def move_left(vis1: o3d.visualization.Visualizer, action, mods):
        nonlocal sphere1, sphere2, center1, center2
        if action == 1:
            if activate_point == 1:
                center1[0] -= MOVE_STEP
                logger.info(f'point1向左移动{MOVE_STEP}, 新坐标为：{center1}')
                sphere1.translate([-MOVE_STEP, 0, 0])
                return True
            elif activate_point == 2:
                center2[0] -= MOVE_STEP
                logger.info(f'point2向左移动{MOVE_STEP}, 新坐标为：{center2}')
                sphere2.translate([-MOVE_STEP, 0, 0])
                return True
        return False

    def move_right(vis1: o3d.visualization.Visualizer, action, mods):
        nonlocal sphere1, sphere2, center1, center2
        if action == 1:
            if activate_point == 1:
                center1[0] += MOVE_STEP
                logger.info(f'point1向右移动{MOVE_STEP}, 新坐标为：{center1}')
                sphere1.translate([MOVE_STEP, 0, 0])
                return True
            elif activate_point == 2:
                center2[0] += MOVE_STEP
                logger.info(f'point2向右移动{MOVE_STEP}, 新坐标为：{center2}')
                sphere2.translate([MOVE_STEP, 0, 0])
                return True
        return False

    def move_front(vis1: o3d.visualization.Visualizer, action, mods):
        nonlocal sphere1, sphere2, center1, center2
        if action == 1:
            if activate_point == 1:
                center1[1] += MOVE_STEP
                logger.info(f'point1向前移动{MOVE_STEP}, 新坐标为：{center1}')
                sphere1.translate([0, MOVE_STEP, 0])
                return True
            elif activate_point == 2:
                center2[1] += MOVE_STEP
                logger.info(f'point2向前移动{MOVE_STEP}, 新坐标为：{center2}')
                sphere2.translate([0, MOVE_STEP, 0])
                return True
        return False

    def move_back(vis1: o3d.visualization.Visualizer, action, mods):
        nonlocal sphere1, sphere2, center1, center2
        if action == 1:
            if activate_point == 1:
                center1[1] -= MOVE_STEP
                logger.info(f'point1向后移动{MOVE_STEP}, 新坐标为：{center1}')
                sphere1.translate([0, -MOVE_STEP, 0])
                return True
            elif activate_point == 2:
                center2[1] -= MOVE_STEP
                logger.info(f'point2向后移动{MOVE_STEP}, 新坐标为：{center2}')
                sphere2.translate([0, -MOVE_STEP, 0])
                return True
        return False

    def smaller_point(vis1: o3d.visualization.Visualizer, action, mods):
        nonlocal r, sphere1, sphere2
        if action == 1:  # key down
            vis1.remove_geometry(sphere1)
            vis1.remove_geometry(sphere2)
            r = r - 0.02 if r - 0.02 > 0 else 0.01
            sphere_new1 = o3d.geometry.TriangleMesh.create_sphere(r)
            sphere_new1.compute_vertex_normals()
            sphere_new1.translate(center1)
            sphere_new1.paint_uniform_color([1., 0., 0.])
            sphere_new2 = o3d.geometry.TriangleMesh.create_sphere(r)
            sphere_new2.compute_vertex_normals()
            sphere_new2.translate(center2)
            sphere_new2.paint_uniform_color([1., 0., 0.])
            vis1.add_geometry(sphere_new1)
            vis1.add_geometry(sphere_new2)
            sphere1 = sphere_new1
            sphere2 = sphere_new2
            return False

        return False

    def bigger_point(vis1: o3d.visualization.Visualizer, action, mods):
        nonlocal r, sphere1, sphere2
        if action == 1:  # key down
            vis1.remove_geometry(sphere1)
            vis1.remove_geometry(sphere2)
            r = r + 0.02
            sphere_new1 = o3d.geometry.TriangleMesh.create_sphere(r)
            sphere_new1.compute_vertex_normals()
            sphere_new1.translate(center1)
            sphere_new1.paint_uniform_color([1., 0., 0.])
            sphere_new2 = o3d.geometry.TriangleMesh.create_sphere(r)
            sphere_new2.compute_vertex_normals()
            sphere_new2.translate(center2)
            sphere_new2.paint_uniform_color([1., 0., 0.])
            vis1.add_geometry(sphere_new1)
            vis1.add_geometry(sphere_new2)
            sphere1 = sphere_new1
            sphere2 = sphere_new2
            return False

        return False

    '''
    “.” 增大点
    “,” 缩小点
    “udlrfb” 控制激活点的上下左右前后的移动
    “1/2” 选择激活的 点1 or 点2
    '''
    vis.register_key_action_callback(ord('.'), bigger_point)
    vis.register_key_action_callback(ord(','), smaller_point)
    vis.register_key_action_callback(ord('U'), move_up)
    vis.register_key_action_callback(ord('D'), move_down)
    vis.register_key_action_callback(ord('L'), move_left)
    vis.register_key_action_callback(ord('R'), move_right)
    vis.register_key_action_callback(ord('F'), move_front)
    vis.register_key_action_callback(ord('B'), move_back)
    vis.register_key_action_callback(ord('1'), activate_point1)
    vis.register_key_action_callback(ord('2'), activate_point2)
    # vis.register_key_action_callback(80, smaller_point)

    screenshot_filename = osp.basename(pcd_filepath1).replace('.pcd', '') + 'with' + \
                          osp.basename(pcd_filepath2).replace('.pcd', '') + '.jpg'
    save_screenshot_filepath = osp.join(
        osp.dirname(pcd_filepath1),
        screenshot_filename
    )
    print(f'请调整质心位置：\n'
          f'\t- “1/2” 选择激活质心1 or 质心2\n'
          f'\t- “u/d/l/r/f/b” 控制激活质心的上下左右前后的移动\n'
          f'\t-     “./,” 增大或缩小质心\n'
          f'\t- ctrl + 0/1/2/3 修改质心颜色\n'
          f'关闭窗口时，将保存当前截图并计算质心距离...')
    vis.run()
    vis.capture_screen_image(save_screenshot_filepath)
    logger.info(f'point cloud1 的中心：{center1}')
    logger.info(f'point cloud2 的中心：{center2}')
    d = compute_distance(center1, center2)
    logger.info(f'两点云中心的距离：{d}')
    vis.destroy_window()


def main():
    print('脚本计算两个点云的质心的距离\n注：程序将在pcd文件同级目录下生成结果')
    while True:
        s1 = input('\n请输入待处理的文件路径1，输入‘exit’结束程序：')
        if s1.lower() == 'exit':
            break
        s2 = input('\n请输入待处理的文件路径2，输入‘exit’结束程序：')
        if s2.lower() == 'exit':
            break

        calculate_distance_between_centers_of_2_pointclouds_script(s1, s2)


if __name__ == '__main__':
    main()
