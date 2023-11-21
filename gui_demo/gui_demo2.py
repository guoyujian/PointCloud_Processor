
import open3d.visualization.gui as gui


class App:
    count = 0

    def __init__(self):
        # 初始化
        gui.Application.instance.initialize()
        self.window = gui.Application.instance.create_window(
            "Event and Widget", 300, 600)

        # 使用相对大小避免直接设置像素，因为不同显示器像素大小可能不同
        em = self.window.theme.font_size

        # 文本框和按钮
        self._push_edit = gui.TextEdit()
        push_button = gui.Button('...')
        push_button.horizontal_padding_em = 0.5
        push_button.vertical_padding_em = 0
        push_button.set_on_clicked(self._on_push_button)

        # 文本框和按钮水平布局
        push_button_layout = gui.Horiz()
        push_button_layout.add_child(gui.Label('Push Button'))
        push_button_layout.add_child(self._push_edit)
        push_button_layout.add_fixed(0.25 * em)
        push_button_layout.add_child(push_button)

        # 总体垂直布局
        self.pannel = gui.Vert()
        self.pannel.add_fixed(0.5 * em)
        self.pannel.add_child(push_button_layout)

        self.window.add_child(self.pannel)

    def _on_push_button(self):
        self.count += 1
        # 设置文本框文字
        self._push_edit.text_value = f'push count {self.count}'
        # 弹出消息框
        self.window.show_message_box('Push Info', 'Hello World!')

    def run(self):
        gui.Application.instance.run()


if __name__ == "__main__":
    app = App()
    app.run()
