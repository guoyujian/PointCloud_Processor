import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering


class App:
    def __init__(self):
        gui.Application.instance.initialize()

        self.window = gui.Application.instance.create_window("layout", 800, 600)
        w = self.window
        em = w.theme.font_size

        # 渲染窗口
        self._scene = gui.SceneWidget()
        self._scene.scene = rendering.Open3DScene(w.renderer)

        # 右侧面板
        self._cttc = gui.ScrollableVert(100, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.254 * em))
        # self._cttc.visible = False
        # self._pannel = gui.Vert(0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.254 * em))
        # for i in range(15):
        #     self._pannel.add_child(gui.Label(f"{i}-th label"))

        # self._button = gui.Button("button")

        # 布局回调函数
        w.set_on_layout(self._on_layout)
        w.add_child(self._scene)
        # w.add_child(self._pannel)
        # w.add_child(self._button)
        w.add_child(self._cttc)

    def _on_layout(self, layout_context):
        #   在on_layout回调函数中应正确设置所有子对象的框架(position + size)，
        #   回调结束之后才会布局孙子对象。
        print(layout_context.theme)
        r = self.window.content_rect
        # print(f'r: {type(r)}')
        self._scene.frame = r

        # pannel_width = 17 * layout_context.theme.font_size
        # pannel_height = min(
        #     r.height, self._pannel.calc_preferred_size(
        #         layout_context, gui.Widget.Constraints()).height
        # )
        # self._pannel.frame = gui.Rect(r.get_right() - pannel_width, r.y, pannel_width, pannel_height)
        #
        # button_pref = self._button.calc_preferred_size(
        #     layout_context, gui.Widget.Constraints())
        # self._button.frame = gui.Rect(r.x, r.get_bottom() - button_pref.height, button_pref.width, button_pref.height)
        # print(r.x, r.y)

        cttc_pref = self._cttc.calc_preferred_size(
            layout_context,
            gui.Widget.Constraints()
        )

        self._cttc.frame = gui.Rect(r.get_right() - cttc_pref.width, r.y, cttc_pref.width, r.get_bottom())

    def run(self):
        gui.Application.instance.run()


if __name__ == "__main__":
    app = App()
    app.run()
