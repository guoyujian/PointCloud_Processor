import random

import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
import pathlib
import os
import os.path as osp
from loguru import logger
from enum import Enum
import numpy as np
import copy
import sys
import platform
from functools import partial




class SceneMode(Enum):
    '''
    枚举类：表示不同的模式
    0 - 展示模式，该模式下可以转动点云视角，但是不能选点、不能对点云进行裁剪等操作
    1 - 选点模式，该模式下可以选择点云中的点
    2 - 编辑模式，该模式下可以选点
    '''

    status_show = 0
    status_pickpoints = 1
    status_edit = 2


isMacOS = (platform.system() == "Darwin")
logger.info(f'isMacOS: {isMacOS}')

class App:
    '''
    主程序类
    '''

    # 菜单唯一标识

    # FILE
    # 打开文件
    MENU_FILE_OPEN = 1
    # 保存点云文件
    MENU_FILE_SAVE = 2
    # 截屏
    MENU_FILE_SCREENSHOT = 3
    # 退出
    MENU_FILE_QUIT = 4

    # GEOMETRY
    # 从pcd文件中添加几何体
    MENU_GEOMETRY_ADD_FROM_PCD = 11
    # 自定义添加球几何体（目前仅支持添加球，为了计算点距离）
    MENU_GEOMETRY_ADD_CUSTOM_SPHERE = 12

    # CALCU
    #计算点到点之间的距离
    MENU_CALCU_DISTANCE_P2P = 21
    # 计算几何体到几何体之间的距离
    MENU_CALCU_DISTANCE_G2G = 22
    # 计算凸包体积
    MENU_CALCU_CONVEX_HULL_VOLUME = 23
    # 计算体积(其它方式，暂未实现)
    MENU_CALCU_VOLUME = 24

    # MODE
    # 展示模式
    MENU_MODE_SHOW = 31
    # 编辑模式
    MENU_MODE_EDIT = 32
    # 选点模式
    MENU_MODE_PCIKPOINTS = 33

    # OPERATE（这些是针对全部点云对象的操作）
    # 下采样（只针对点云）
    MENU_OPERATE_DOWNSAMPLE = 42
    # 赋色（只针对点云）
    MENU_OPERATE_COLORATION = 43
    # 移动
    MENU_OPERATE_MOVE = 44

    # SHOW
    # 显示坐标系
    MENU_SHOW_COORDINATE_AXIS = 51
    # 显示右侧面板（包含几何面板、点面板、属性面板）
    MENU_SHOW_RIGHTSIDE_PANEL = 52




    # 关闭文件
    # MENU_CLOSE = 2
    # MENU_PICK_POINTS = 3
    # MENU_SHOW = 5
    #
    # # 关闭窗口
    # MENU_QUIT = 20
    # # 关于
    # MENU_ABOUT = 21
    #
    # show = True

    # 几何列表，存放几何体对象
    _geometries = []
    # 是否显示列表，对应每个几何体是否应该显示
    _geometries_shown = []
    # 活跃状态的几何体idx
    _active_geometries_idx = -1
    # 新的几何体的idx
    _next_idx = 0

    # 保存被选中点的序号（在点云中的序号）
    _picked_indicates = []
    # 被选中点的坐标
    _picked_points = []
    # 被选中点的数量
    _pick_num = 0
    # 被选中点的3d label
    _label3d_list = []

    # 场景模式
    _scene_mode = SceneMode.status_show

    def __init__(self, resource_path):
        # 初始化
        gui.Application.instance.initialize(resource_path)

        # 窗口
        self.window = gui.Application.instance.create_window("myApp", 800, 600)
        w = self.window
        # 使用相对大小避免直接设置像素，因为不同显示器像素大小可能不同
        em = w.theme.font_size

        # 主场景
        self._scene = gui.SceneWidget()
        self._scene.scene = rendering.Open3DScene(w.renderer)
        # 默认不展示坐标轴
        self._scene.scene.show_axes(False)


        # 设置鼠标事件
        self._scene.set_on_mouse(self._mouse_event)

        # self._scene.set_view_controls(gui.SceneWidget.Controls.PICK_POINTS)

        # 设置菜单栏
        # self._test = gui.ListView()
        # self._test.set_items(['a','b'])



        # 右侧面板
        self._rightside_panel = gui.ScrollableVert(0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.254 * em))
        self._geometry_panel = gui.CollapsableVert('Geometries', 0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.254 * em))
        self._geometry_panel_title = gui.Horiz(0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.254 * em))
        self._geometry_panel_title.add_child(gui.Label(f'Geometry Name'))
        self._geometry_panel_title.add_child(gui.Label(f'Visible'))
        self._geometry_panel_title.add_child(gui.Label(f'Active'))
        self._geometry_panel_title.add_child(gui.Label(f'Operate'))
        self._geometry_panel.add_child(self._geometry_panel_title)
        self._geometry_panel_items = gui.WidgetProxy()
        self._geometry_panel.add_child(self._geometry_panel_items)




        # self._geometry_panel_line0 = gui.Horiz(0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.254 * em))
        # self._geometry_panel_line0.add_child(gui.Label(f'Geometry 1'))
        # self._geometry_panel_line0.add_child(gui.Checkbox(f''))
        # self._geometry_panel_line0.add_child(gui.Checkbox(f''))
        # self._geometry_panel_line0.add_child(gui.Button(f'Remove'))
        # self._geometry_panel.add_child(self._geometry_panel_line0)



        self._point_panel = gui.CollapsableVert('Points', 0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.254 * em))
        self._attribute_panel = gui.CollapsableVert('Attribute', 0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.254 * em))
        self._rightside_panel.add_child(self._geometry_panel)
        self._rightside_panel.add_child(self._point_panel)
        self._rightside_panel.add_child(self._attribute_panel)

        # self._rightside_panel.visible = False
        # self._pannel = gui.CollapsableVert('panel', 0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.25 * em))
        # for i in range(15):
        #     self._pannel.add_child(gui.Label(f"{i}-th label"))

        # self._button = gui.Button("button")

        # 左下角提示信息
        self._info = gui.Label("")
        self._info.visible = False

        # 布局回调函数
        w.set_on_layout(self._on_layout)
        w.add_child(self._scene)
        w.add_child(self._info)
        w.add_child(self._rightside_panel)
        # w.add_child(self._pannel)
        # w.add_child(self._button)

        # ---------------Menu----------------
        # 菜单栏是全局的（因为macOS上是全局的）
        # 无论创建多少窗口，菜单栏只创建一次。



        # 布局回调函数


        # ----以下只针对Windows的菜单栏创建----
        # mac不支持子菜单栏
        if gui.Application.instance.menubar is None:
            # 文件菜单栏
            file_menu = gui.Menu()
            file_menu.add_item("Open...", App.MENU_FILE_OPEN)
            file_menu.add_item("Save PCD", App.MENU_FILE_SAVE)
            file_menu.add_separator()
            file_menu.add_item("Scree Shot", App.MENU_FILE_SCREENSHOT)
            file_menu.add_separator()
            file_menu.add_item("Quit", App.MENU_FILE_QUIT)


            geometry_menu = gui.Menu()
            geometry_menu.add_item("Add Geometry From PCD", App.MENU_GEOMETRY_ADD_FROM_PCD)
            # 几何体菜单栏
            if isMacOS:
                # mac不支持子菜单栏? 所以这里使用平行菜单
                geometry_menu.add_separator()
                geometry_menu.add_item("Add Custom Sphere", App.MENU_GEOMETRY_ADD_CUSTOM_SPHERE)
            else:
                geometry_sub_menu1 = gui.Menu()
                geometry_sub_menu1.add_item("Sphere", App.MENU_GEOMETRY_ADD_CUSTOM_SPHERE)
                geometry_menu.add_menu("Add Gemotry Custom...", geometry_sub_menu1)

            # 计算菜单栏
            calcu_menu = gui.Menu()
            if isMacOS:
                calcu_menu.add_item("P2P Distance", App.MENU_CALCU_DISTANCE_P2P)
                calcu_menu.add_item("G2G Distance", App.MENU_CALCU_DISTANCE_G2G)
                calcu_menu.add_item("Convex Hull Volume", App.MENU_CALCU_CONVEX_HULL_VOLUME)
                calcu_menu.add_item("Other Volume", App.MENU_CALCU_VOLUME)
                pass
            else:
                calcu_sub_menu_distance = gui.Menu()
                calcu_sub_menu_distance.add_item("P2P", App.MENU_CALCU_DISTANCE_P2P)
                calcu_sub_menu_distance.add_item("G2G", App.MENU_CALCU_DISTANCE_G2G)

                calcu_menu.add_menu("distance", calcu_sub_menu_distance)

                calcu_sub_menu_volume = gui.Menu()
                calcu_sub_menu_volume.add_item("Convex Hull Volume", App.MENU_CALCU_CONVEX_HULL_VOLUME)
                calcu_sub_menu_volume.add_item("Other", App.MENU_CALCU_VOLUME)

                calcu_menu.add_menu("volume", calcu_sub_menu_volume)


            # mode menu
            mode_menu = gui.Menu()
            mode_menu.add_item("Show", App.MENU_MODE_SHOW)
            mode_menu.add_item("Edit", App.MENU_MODE_EDIT)
            mode_menu.add_item("Pick Points", App.MENU_MODE_PCIKPOINTS)
            # 默认是展示模式
            mode_menu.set_checked(App.MENU_MODE_SHOW, True)
            self.mode_menu = mode_menu

            # operate menu
            operate_menu = gui.Menu()
            operate_menu.add_item("Coloration", App.MENU_OPERATE_COLORATION)
            operate_menu.add_item("Sample", App.MENU_OPERATE_DOWNSAMPLE)
            operate_menu.add_item("MOVE", App.MENU_OPERATE_MOVE)

            # show menu
            show_menu = gui.Menu()
            show_menu.add_item("Coordinate Axis", App.MENU_SHOW_COORDINATE_AXIS)
            show_menu.add_item("RightSide Panel", App.MENU_SHOW_RIGHTSIDE_PANEL)
            self.show_menu = show_menu


            # 菜单栏
            menu = gui.Menu()
            # MacOS会自动把第一个菜单的名字命名为应用的名字...
            menu.add_menu("File", file_menu)
            menu.add_menu("Geometry", geometry_menu)
            menu.add_menu("Calculate", calcu_menu)
            menu.add_menu("Mode", mode_menu)
            menu.add_menu("Show", show_menu)


            gui.Application.instance.menubar = menu

            # -----注册菜单栏事件------
            w.set_on_menu_item_activated(App.MENU_FILE_OPEN, self._menu_file_open)
            w.set_on_menu_item_activated(App.MENU_FILE_SAVE, self._menu_file_save)
            w.set_on_menu_item_activated(App.MENU_FILE_SCREENSHOT, self._menu_file_screenshot)
            w.set_on_menu_item_activated(App.MENU_FILE_QUIT, self._menu_file_quit)

            w.set_on_menu_item_activated(App.MENU_GEOMETRY_ADD_FROM_PCD, self._menu_geometry_add_from_pcd)
            w.set_on_menu_item_activated(App.MENU_GEOMETRY_ADD_CUSTOM_SPHERE, self._menu_geometry_add_custom_sphere)

            w.set_on_menu_item_activated(App.MENU_CALCU_DISTANCE_P2P, self._menu_calcu_distance_p2p)
            w.set_on_menu_item_activated(App.MENU_CALCU_DISTANCE_G2G, self._menu_calcu_distance_g2g)
            w.set_on_menu_item_activated(App.MENU_CALCU_CONVEX_HULL_VOLUME, self._menu_calcu_convex_hull_volume)
            w.set_on_menu_item_activated(App.MENU_CALCU_VOLUME, self._menu_calcu_volume)

            w.set_on_menu_item_activated(App.MENU_MODE_SHOW, self._menu_mode_show)
            w.set_on_menu_item_activated(App.MENU_MODE_EDIT, self._menu_mode_edit)
            w.set_on_menu_item_activated(App.MENU_MODE_PCIKPOINTS, self._menu_mode_pickpoints)

            w.set_on_menu_item_activated(App.MENU_OPERATE_COLORATION, self._menu_operate_coloration)
            w.set_on_menu_item_activated(App.MENU_OPERATE_DOWNSAMPLE, self._menu_operate_downsample)
            w.set_on_menu_item_activated(App.MENU_OPERATE_MOVE, self._menu_operate_move)

            w.set_on_menu_item_activated(App.MENU_SHOW_COORDINATE_AXIS, self._menu_show_coordinate_axis)
            w.set_on_menu_item_activated(App.MENU_SHOW_RIGHTSIDE_PANEL, self._menu_show_rightside_panel)


    def update_geometries_list(self):
        pass
    def _menu_show_rightside_panel(self):
        pass
    def _menu_show_coordinate_axis(self):
        '''
        坐标轴展示
        :return:
        '''
        # 默认不展示坐标轴

        curr_shown_flag = self.show_menu.is_checked(App.MENU_SHOW_COORDINATE_AXIS)
        logger.info("close axis" if curr_shown_flag else "show axis")
        curr_shown_flag = not curr_shown_flag
        self.show_menu.set_checked(App.MENU_SHOW_COORDINATE_AXIS, curr_shown_flag)
        self._scene.scene.show_axes(curr_shown_flag)
        pass

    def _menu_operate_move(self):
        pass
    def _menu_operate_downsample(self):
        pass
    def _menu_operate_coloration(self):
        pass
    def _menu_mode_edit(self):
        # 将scene状态切换至选点状态
        logger.info(f'切换至编辑状态')
        self._scene_mode = SceneMode.status_edit
        self.mode_menu.set_checked(App.MENU_MODE_SHOW, False)
        self.mode_menu.set_checked(App.MENU_MODE_PCIKPOINTS, False)
        self.mode_menu.set_checked(App.MENU_MODE_EDIT, True)
        pass
    def _menu_mode_show(self):
        # 将scene状态切换至选点状态
        logger.info(f'切换至展示状态')
        self._scene_mode = SceneMode.status_edit
        self.mode_menu.set_checked(App.MENU_MODE_SHOW, True)
        self.mode_menu.set_checked(App.MENU_MODE_PCIKPOINTS, False)
        self.mode_menu.set_checked(App.MENU_MODE_EDIT, False)
        pass
    def _menu_calcu_volume(self):
        '''
        TODO: 其他计算体积的方法
        :return:
        '''
        pass


    def _menu_calcu_convex_hull_volume(self):
        '''
        计算凸包体积
        :return:
        '''
        if self._active_geometries_idx >= 0:
            model = self._geometries[self._active_geometries_idx]
            hull, _ = model.compute_convex_hull()
            hull: o3d.geometry.TriangleMesh
            volume = hull.get_volume()
            logger.info(f'几何体 {self._active_geometries_idx}的凸包体积：{volume}')

            volume_dialog = gui.Dialog("convex hull volume")
            volume_res_label = gui.Label(f'Convex Hull Volume of Geometry {self._active_geometries_idx}: {volume} m3')
            ok_button = gui.Button('ok')
            # ok_button.frame()
            def ok():
                self.window.close_dialog()
            ok_button.set_on_clicked(ok)
            vert_layout = gui.Vert()
            vert_layout.add_child(volume_res_label)
            vert_layout.add_child(ok_button)
            volume_dialog.add_child(vert_layout)
            self.window.show_dialog(volume_dialog)
        else:
            logger.info(f'没有加载任何模型')

        pass

    def _menu_calcu_distance_g2g(self):
        pass

    def _menu_calcu_distance_p2p(self):
        pass

    def _menu_geometry_add_custom_sphere(self):
        '''
        向场景中增加一个球，设置半径，球心
        :return:
        '''
        # 创建球心x输入框
        x_input = gui.NumberEdit(gui.NumberEdit.Type.DOUBLE)
        # 创建球心x输入框
        y_input = gui.NumberEdit(gui.NumberEdit.Type.DOUBLE)
        # 创建球心x输入框
        z_input = gui.NumberEdit(gui.NumberEdit.Type.DOUBLE)
        # 创建球半径输入框
        r_input = gui.NumberEdit(gui.NumberEdit.Type.DOUBLE)

        line1 = gui.Horiz()
        line1.add_child(gui.Label("x:"))
        line1.add_child(x_input)

        line2 = gui.Horiz()
        line2.add_child(gui.Label("y:"))
        line2.add_child(y_input)

        line3 = gui.Horiz()
        line3.add_child(gui.Label("z:"))
        line3.add_child(z_input)

        line4 = gui.Horiz()
        line4.add_child(gui.Label("r:"))
        line4.add_child(r_input)

        line5 = gui.Horiz()
        cancel_button = gui.Button("Cancel")
        confirm_button = gui.Button("Confirm")
        def cancel():
            '''
            取消按钮事件
            :return:
            '''
            self.window.close_dialog()
        def confirm():
            '''
            确认按钮事件
            :return:
            '''
            logger.info(f'sphere center: ({x_input.double_value}, {y_input.double_value}, {z_input.double_value});'
                        f'r: {r_input.double_value}')
            center = np.array([x_input.double_value, y_input.double_value, z_input.double_value])
            sphere = o3d.geometry.TriangleMesh.create_sphere(r_input.double_value)
            sphere.translate(center)
            sphere.paint_uniform_color(np.array([random.random(), random.random(), random.random()]))
            logger.info(f'add a sphere, idx: {self._next_idx}')
            self.add_a_geometry(sphere)
            self.window.close_dialog()
        cancel_button.set_on_clicked(cancel)
        confirm_button.set_on_clicked(confirm)
        line5.add_child(cancel_button)
        line5.add_child(confirm_button)

        panel = gui.Vert()
        panel.add_child(line1)
        panel.add_child(line2)
        panel.add_child(line3)
        panel.add_child(line4)
        panel.add_child(line5)

        dialog = gui.Dialog("input params")
        dialog.add_child(panel)
        self.window.show_dialog(dialog)

        pass

    def _menu_geometry_add_from_pcd(self):
        pass

    def _menu_file_quit(self):
        '''
        退出应用
        :return:
        '''
        self.window.close()
        pass


    def _menu_file_screenshot(self):
        pass



    def _menu_file_save(self):
        '''
        保存文件
        :return:
        '''
        pass


    def _menu_file_open(self):
        '''
        打开文件
        :return:
        '''
        # 文件拾取对话框
        file_picker = gui.FileDialog(gui.FileDialog.OPEN, "Select File...", self.window.theme)

        # 文件类型过滤
        # file_picker.add_filter('.obj', 'obj model files')
        file_picker.add_filter('.pcd', 'Point Cloud Data Files')
        # file_picker.add_filter('', 'All files')

        # 初始文件路径
        file_picker.set_path(osp.join(str(pathlib.Path.home()), 'Desktop'))

        # 设置对话框按钮回调
        file_picker.set_on_cancel(self._menu_file_open_on_cancel)
        file_picker.set_on_done(self._menu_file_open_on_done)

        # 显示对话框
        self.window.show_dialog(file_picker)


    def _menu_mode_pickpoints(self):
        '''
        选点mode
        :return:
        '''
        logger.info(f'切换至选点状态')
        self._scene_mode = SceneMode.status_pickpoints
        self.mode_menu.set_checked(App.MENU_MODE_SHOW, False)
        self.mode_menu.set_checked(App.MENU_MODE_PCIKPOINTS, True)
        self.mode_menu.set_checked(App.MENU_MODE_EDIT, False)
        pass





    def _menu_file_open_on_cancel(self):
        '''
        当取消 打开文件 时
        :return:
        '''
        self.window.close_dialog()

    def _menu_file_open_on_done(self, filepath):
        '''
        选择打开文件后的回调函数
        :param filename:
        :return:
        '''
        self.window.close_dialog()
        self.load(filepath)


    def clear_all_geometries(self):
        '''
        清空所有的几何体
        :return:
        '''
        self._geometries = []
        # 是否显示，key是geometry的name，value是 是否显示
        self._geometries_shown = []
        # 激活的几何体name
        self._active_geometries_idx = -1
        self._next_idx = 0
        self._scene.scene.clear_geometry()


    def _geometries_num(self):
        '''
        TODO: 计算self._geometries列表中有效的几何体数量
        :return:
        '''
        return sum([1 if _ else 0 for _ in self._geometries])

    def refresh_geometries_list(self):
        '''
        更新右侧几何体列表
        :return:
        '''
        logger.info(f'更新几何体列表，数量：{self._geometries_num()}')
        em = self.window.theme.font_size
        self._geometry_panel_items.set_widget(None)
        # self._geometry_panel = gui.CollapsableVert('Geometries', 0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.254 * em))
        # self._geometry_panel.add_child(self._geometry_panel_title)
        widget = gui.Vert()

        def switch_visible(geometry_idx, bool):
            '''
            点击是否可见checkbox时触发的事件
            :param geometry_idx:
            :param bool:
            :return:
            '''
            self._scene.scene.show_geometry(str(geometry_idx), bool)
            self._geometries_shown[geometry_idx] = bool
            logger.info(('展示' if bool else '隐藏') + f' 几何体 {geometry_idx}')


        def switch_active(geometry_idx, bool):
            '''
            点击激活checkbox时触发的事件
            :param geometry_idx:
            :param bool:
            :return:
            '''
            if geometry_idx == self._active_geometries_idx or not bool:
                # 不能取消勾选激活状态下的几何体，只能通过激活其他几何体来切换
                logger.info(f'不能取消勾选激活状态下的几何体，只能通过激活其他几何体来实现切换')
                new_active_checkbox = \
                self._geometry_panel_items.get_widget().get_children()[geometry_idx].get_children()[2]
                new_active_checkbox.checked = True
                return gui.Checkbox.IGNORED
            logger.info(f'switch active geometry idx {self._active_geometries_idx} to {geometry_idx}')
            new_active_checkbox = self._geometry_panel_items.get_widget().get_children()[geometry_idx].get_children()[2]
            new_active_checkbox.checked = bool
            old_active_checkbox = self._geometry_panel_items.get_widget().get_children()[self._active_geometries_idx].get_children()[2]
            old_active_checkbox.checked = False
            self._active_geometries_idx = geometry_idx

        def remove_geometry_button_event(geometry_idx):
            '''
            点击remove按钮时触发的事件
            :param geometry_idx:
            :return:
            '''
            if self._active_geometries_idx == geometry_idx:
                logger.info(f'不能移除活动状态下的几何体')
                return gui.Button.IGNORED
            self._geometries[geometry_idx] = None
            self._scene.scene.remove_geometry(str(geometry_idx))
            self.refresh_geometries_list()

        for i, _ in enumerate(self._geometries):
            if not _:
                continue
            geometry_panel_line = gui.Horiz(0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.254 * em))
            geometry_panel_line.add_child(gui.Label(f'{i}'))
            visible_checkbox = gui.Checkbox(f'')
            visible_checkbox.checked = self._geometries_shown[i]
            visible_checkbox.set_on_checked(partial(switch_visible, i))
            geometry_panel_line.add_child(visible_checkbox)
            active_checkbox = gui.Checkbox(f'')
            active_checkbox.checked = i == self._active_geometries_idx
            active_checkbox.set_on_checked(partial(switch_active, i))
            geometry_panel_line.add_child(active_checkbox)
            remove_button = gui.Button(f'Remove')
            remove_button.set_on_clicked(partial(remove_geometry_button_event, i))
            geometry_panel_line.add_child(remove_button)
            widget.add_child(geometry_panel_line)
        self._geometry_panel_items.set_widget(widget)
        # self.window.set_on_layout(self._on_layout)
        # self.window.add_child(self._geometry_panel)
        # self._rightside_panel.add_fixed(3)
        # self.window.post_redraw()
        self.window.set_needs_layout()



    def add_a_geometry(self, geometry):
        '''
        增加一个几何体，并将该几何体设置为active
        :return:
        '''
        if self._active_geometries_idx == -1:
            # 场景为空，此时需要设置相机
            bounds = geometry.get_axis_aligned_bounding_box()
            self._scene.setup_camera(60, bounds, bounds.get_center())
        # 定义材质
        material = rendering.MaterialRecord()
        material.sRGB_color = True
        # material.shader = 'normals'

        # 向场景中添加模型

        self._geometries.append(geometry)
        self._geometries_shown.append(True)
        self._scene.scene.add_geometry(str(self._next_idx), geometry, material)
        self._active_geometries_idx = self._next_idx
        self._next_idx += 1
        self.refresh_geometries_list()

        # 重绘
        self._scene.force_redraw()


    def load(self, filepath):
        '''
        加载pcd文件到场景中
        :param filepath:
        :return:
        '''
        logger.info(f'open filename: {filepath}')
        logger.info(f'clear previous geometries')
        # 清空之前的几何体
        self.clear_all_geometries()

        # 读取模型文件
        geometry: o3d.geometry.PointCloud = o3d.io.read_point_cloud(filepath)

        logger.info(f'add a geometry idx : {self._next_idx}')
        self.add_a_geometry(geometry)


    # 切换显示模型
    # def _menu_show(self):
    #     self.show = not self.show
    #     gui.Application.instance.menubar.set_checked(App.MENU_SHOW, self.show)
    #     self._scene.scene.show_geometry('bunny', self.show)

    def _on_layout(self, layout_context):
        #   在on_layout回调函数中应正确设置所有子对象的框架(position + size)，
        #   回调结束之后才会布局孙子对象。

        r = self.window.content_rect
        self._scene.frame = r

        # 配置左下角信息label
        _size_info = self._info.calc_preferred_size(layout_context, gui.Widget.Constraints())
        self._info.frame = gui.Rect(
            r.x, r.get_bottom() - _size_info.height, _size_info.width, _size_info.height)

        # 右侧面板layout
        _size_rightside_panel = self._rightside_panel.calc_preferred_size(layout_context, gui.Widget.Constraints())
        self._rightside_panel.frame = gui.Rect(r.get_right() - _size_rightside_panel.width, r.y,
                                                _size_rightside_panel.width, r.get_bottom())

        # _size_test = self._test.calc_preferred_size(layout_context, gui.Widget.Constraints())
        # self._test.frame = gui.Rect(r.get_right() - _size_test.width, r.y,
        #                                         _size_test.width, r.get_bottom())




        # pannel_width = 17 * layout_context.theme.font_size
        # pannel_height = min(
        #     r.height, self._pannel.calc_preferred_size(
        #         layout_context, gui.Widget.Constraints()).height
        # )
        # self._pannel.frame = gui.Rect(r.get_right() - pannel_width, r.y, pannel_width, pannel_height)

        # button_pref = self._button.calc_preferred_size(
        #     layout_context, gui.Widget.Constraints())
        # self._button.frame = gui.Rect(r.x, r.get_bottom() - button_pref.height, button_pref.width, button_pref.height)

    def run(self):
        gui.Application.instance.run()

    def _calc_prefer_indicate(self, geo, point):
        '''
        根据世界坐标搜索点云坐标，返回在选中点在点云中的索引值
        :param self:
        :param point:
        :return:
        '''
        pcd_tree = o3d.geometry.KDTreeFlann(geo)
        [k, picked_idx, _] = pcd_tree.search_knn_vector_3d(point, 1)
        return picked_idx[-1]

    def _mouse_event(self, event):
        '''
        鼠标事件
        :return:
        '''
        if (self._scene_mode == SceneMode.status_pickpoints and event.type == gui.MouseEvent.Type.BUTTON_DOWN
                and event.is_button_down(gui.MouseButton.LEFT) and event.is_modifier_down(gui.KeyModifier.CTRL)):
            # 选点模式下，按住ctrl+鼠标左键进行选点操作

            if self._active_geometries_idx < 0:
                # 没有任何几何体，试图选点
                logger.info(f'至少要加载一个几何体')
                return gui.Widget.EventCallbackResult.IGNORED

            # 获得操作对象
            geo = self._geometries[self._active_geometries_idx]
            assert geo
            logger.info(f'选点...')

            def depth_callback(depth_image):

                x = event.x - self._scene.frame.x
                y = event.y - self._scene.frame.y

                depth = np.asarray(depth_image)[y, x]

                if depth == 1.0:
                    # 远平面（没有几何体）
                    text = ""
                else:
                    world = self._scene.scene.camera.unproject(x, y, depth,
                                                               self._scene.frame.width, self._scene.frame.height)

                    text = "({:.3f}, {:.3f}, {:.3f})".format(world[0], world[1], world[2])

                    idx = self._calc_prefer_indicate(geo, world)
                    true_point = np.asarray(geo.points)[idx]

                    self._pick_num += 1
                    self._picked_indicates.append(idx)
                    self._picked_points.append(true_point)

                    logger.info(f"Pick point #{idx} at ({true_point}")

                def draw_point():
                    self._info.text = text
                    self._info.visible = (text != "")
                    self.window.set_needs_layout()

                    if depth != 1.0:
                        label3d = self._scene.add_3d_label(true_point, "#" + str(self._pick_num))
                        self._label3d_list.append(label3d)

                        # 标记球
                        sphere = o3d.geometry.TriangleMesh.create_sphere(0.1)
                        sphere.paint_uniform_color([1, 0, 0])
                        sphere.translate(true_point)
                        material = rendering.MaterialRecord()
                        material.shader = 'defaultUnlit'
                        self._scene.scene.add_geometry("point" + str(self._pick_num), sphere, material)
                        self._scene.force_redraw()

                gui.Application.instance.post_to_main_thread(self.window, draw_point)

            self._scene.scene.scene.render_to_depth_image(depth_callback)
            return gui.Widget.EventCallbackResult.HANDLED
        elif (self._scene_mode == SceneMode.status_pickpoints and event.type == gui.MouseEvent.Type.BUTTON_DOWN
                and event.is_button_down(gui.MouseButton.RIGHT)):
            # 选点模式下，点击鼠标右键取消选中的点
            if self._pick_num > 0:
                idx = self._picked_indicates.pop()
                point = self._picked_points.pop()

                logger.info(f"Undo pick: #{idx} at ({point})")
                self._scene.scene.remove_geometry('point' + str(self._pick_num))
                self._pick_num -= 1
                self._scene.remove_3d_label(self._label3d_list.pop())
                self._scene.force_redraw()
            else:
                logger.info("Undo no point!")
            return gui.Widget.EventCallbackResult.HANDLED
        return gui.Widget.EventCallbackResult.IGNORED


def main():
    logger.info("Run in python process!")
    resource_path = 'resources'
    resource_path = osp.abspath(resource_path)

    logger.info("Resources:", resource_path)

    app = App(resource_path)
    app.run()


if __name__ == "__main__":
    main()
