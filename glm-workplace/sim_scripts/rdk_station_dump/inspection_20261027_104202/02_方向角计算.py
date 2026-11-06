import math
import tkinter as tk
from tkinter import ttk, messagebox

from robodk.robomath import Mat, Pose_2_Fanuc


# ============================================================
# 法兰坐标系 X+/Y+/Z+ -> RoboDK Fanuc/Motoman Rxyz
#
# 重要定义：
#   本程序现在不再只使用“末端朝向 Z 轴”计算姿态。
#   因为仅指定 Z+ 只能确定法兰朝向，不能确定绕 Z+ 的旋转。
#
#   现在可以同时输入：
#       X+ 在世界坐标中的方向
#       Y+ 在世界坐标中的方向
#       Z+ 在世界坐标中的方向
#
#   三个轴共同决定完整的法兰姿态。
#
#   如果只知道 Z+：
#       可以使用“Z+ + X+参考方向”模式，
#       程序会自动把 X+参考方向投影到垂直于 Z+ 的平面。
#
# 输出：
#   RoboDK Fanuc/Motoman [X,Y,Z,Rx,Ry,Rz]
#
# 单位：
#   输入向量：无单位，只表示方向
#   Rxyz：deg
# ============================================================


def vec_length(v):
    return math.sqrt(
        v[0] * v[0] +
        v[1] * v[1] +
        v[2] * v[2]
    )


def normalize(v):
    length = vec_length(v)

    if length < 1e-12:
        raise ValueError("方向向量不能为零向量")

    return (
        v[0] / length,
        v[1] / length,
        v[2] / length
    )


def dot(a, b):
    return (
        a[0] * b[0] +
        a[1] * b[1] +
        a[2] * b[2]
    )


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
    )


def scale(v, s):
    return (
        v[0] * s,
        v[1] * s,
        v[2] * s
    )


def sub(a, b):
    return (
        a[0] - b[0],
        a[1] - b[1],
        a[2] - b[2]
    )


def axis_to_rxyz(x_axis, y_axis, z_axis):
    """
    已知完整的法兰坐标系 X+/Y+/Z+ 在世界坐标中的方向，
    构造旋转矩阵并转换为 RoboDK Fanuc/Motoman Rxyz。
    """

    # 三个轴都归一化
    x_axis = normalize(x_axis)
    y_axis = normalize(y_axis)
    z_axis = normalize(z_axis)

    # 基本正交性检查
    xy = abs(dot(x_axis, y_axis))
    yz = abs(dot(y_axis, z_axis))
    zx = abs(dot(z_axis, x_axis))

    if max(xy, yz, zx) > 0.02:
        raise ValueError(
            "输入的 X+/Y+/Z+ 不是相互垂直的坐标轴。\n"
            "请检查三个方向向量。"
        )

    # 右手系检查：
    # X × Y 应该等于 Z
    cross_xy = normalize(cross(x_axis, y_axis))
    if dot(cross_xy, z_axis) < 0:
        raise ValueError(
            "输入的 X+/Y+/Z+ 不是右手坐标系。\n"
            "必须满足 X+ × Y+ = Z+。"
        )

    pose = Mat([
        [x_axis[0], y_axis[0], z_axis[0], 0],
        [x_axis[1], y_axis[1], z_axis[1], 0],
        [x_axis[2], y_axis[2], z_axis[2], 0],
        [0,         0,         0,         1]
    ])

    fanuc = Pose_2_Fanuc(pose)

    return (
        fanuc[3],
        fanuc[4],
        fanuc[5],
        pose
    )


def z_and_x_reference_to_rxyz(z_direction, x_reference):
    """
    已知 Z+ 方向，以及一个“X+参考方向”，
    自动构造完整右手坐标系。

    X+参考方向不要求本身严格垂直 Z+。
    程序会把它投影到垂直于 Z+ 的平面。
    """

    z_axis = normalize(z_direction)
    x_ref = normalize(x_reference)

    # X参考方向投影到垂直 Z+ 的平面
    x_axis = sub(
        x_ref,
        scale(z_axis, dot(x_ref, z_axis))
    )

    if vec_length(x_axis) < 1e-8:
        raise ValueError(
            "Z+ 与 X+参考方向平行或接近平行，"
            "无法确定滚转方向。"
        )

    x_axis = normalize(x_axis)

    # 右手系：X × Y = Z
    # 因此 Y = Z × X
    y_axis = normalize(cross(z_axis, x_axis))

    return axis_to_rxyz(x_axis, y_axis, z_axis)


def rotate_flange_z(pose, angle_deg):
    """绕法兰自身 Z+ 轴右手旋转；从 Z+ 端朝原点看，正角为逆时针。"""
    if not math.isfinite(angle_deg):
        raise ValueError("旋转角度必须是有限数字。")
    angle = math.radians(angle_deg)
    c, s = math.cos(angle), math.sin(angle)
    rotation = Mat([
        [c, -s, 0, 0],
        [s,  c, 0, 0],
        [0,  0, 1, 0],
        [0,  0, 0, 1]
    ])
    # 右乘表示绕局部轴旋转，而不是基座 Z 轴。
    rotated = pose * rotation
    values = Pose_2_Fanuc(rotated)
    return values[3], values[4], values[5], rotated


class DirectionToRxyzGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CR5 法兰坐标系 → RoboDK Rxyz")
        self.root.geometry("960x880")
        self.root.minsize(900, 800)

        self.mode = tk.StringVar(value="full")
        self.rotation_var = tk.StringVar(value="0")
        self.rotation_direction = tk.StringVar(value="顺时针")

        self.x_vars = [tk.StringVar() for _ in range(3)]
        self.y_vars = [tk.StringVar() for _ in range(3)]
        self.z_vars = [tk.StringVar() for _ in range(3)]

        self._build_ui()

        # 默认使用你目前讨论的方向。
        # 注意：这里给的是“法兰 Z+”，不是工具 Z-。
        self._set_axis(self.z_vars, 0, -1, 0)

        # 一组与 Z+=(0,-1,0) 配套的右手坐标系：
        # X+=(1,0,0)
        # Y+=(0,0,1)
        self._set_axis(self.x_vars, 1, 0, 0)
        self._set_axis(self.y_vars, 0, 0, 1)

        self.calculate()

    def _build_ui(self):
        ttk.Label(
            self.root,
            text="CR5 法兰坐标系 X+/Y+/Z+ → RoboDK Fanuc/Motoman Rxyz",
            font=("Microsoft YaHei UI", 16, "bold")
        ).pack(pady=(15, 5))

        ttk.Label(
            self.root,
            text=(
                "现在同时考虑红色 X+、绿色 Y+、蓝色 Z+。"
                "三根轴共同决定完整姿态。"
            ),
            font=("Microsoft YaHei UI", 10)
        ).pack(pady=(0, 12))

        # ====================================================
        # 模式选择
        # ====================================================
        mode_frame = ttk.LabelFrame(
            self.root,
            text="计算方式",
            padding=10
        )
        mode_frame.pack(fill="x", padx=18, pady=6)

        ttk.Radiobutton(
            mode_frame,
            text="完整坐标轴模式：输入 X+ / Y+ / Z+",
            variable=self.mode,
            value="full",
            command=self._update_mode
        ).pack(anchor="w")

        ttk.Radiobutton(
            mode_frame,
            text="方向 + 滚转参考模式：输入 Z+，再给一个 X+参考方向",
            variable=self.mode,
            value="zx",
            command=self._update_mode
        ).pack(anchor="w", pady=(5, 0))

        # ====================================================
        # 完整坐标轴输入
        # ====================================================
        self.full_frame = ttk.LabelFrame(
            self.root,
            text="1A. 法兰三个正方向（世界坐标）",
            padding=10
        )
        self.full_frame.pack(fill="x", padx=18, pady=6)

        self._build_axis_row(
            self.full_frame, "X+（红色）", self.x_vars, 0
        )
        self._build_axis_row(
            self.full_frame, "Y+（绿色）", self.y_vars, 1
        )
        self._build_axis_row(
            self.full_frame, "Z+（蓝色）", self.z_vars, 2
        )

        # ====================================================
        # Z+ + X参考输入
        # ====================================================
        self.zx_frame = ttk.LabelFrame(
            self.root,
            text="1B. Z+方向 + X+滚转参考",
            padding=10
        )

        self._build_axis_row(
            self.zx_frame, "Z+（蓝色）", self.z_vars, 0
        )
        self._build_axis_row(
            self.zx_frame, "X+参考（红色）", self.x_vars, 1
        )

        # ====================================================
        # 快速测试
        # ====================================================
        preset_frame = ttk.LabelFrame(
            self.root,
            text="快速测试",
            padding=10
        )
        preset_frame.pack(fill="x", padx=18, pady=6)

        ttk.Button(
            preset_frame,
            text="图中方向：Z+=(0,-1,0)",
            command=self.preset_current
        ).pack(side="left", padx=5)

        ttk.Button(
            preset_frame,
            text="Z+=+X",
            command=lambda: self.preset_z(1, 0, 0)
        ).pack(side="left", padx=5)

        ttk.Button(
            preset_frame,
            text="Z+=+Y",
            command=lambda: self.preset_z(0, 1, 0)
        ).pack(side="left", padx=5)

        ttk.Button(
            preset_frame,
            text="Z+=+Z",
            command=lambda: self.preset_z(0, 0, 1)
        ).pack(side="left", padx=5)

        rotation_frame = ttk.LabelFrame(
            self.root, text="末端追加旋转（绕法兰自身 Z 轴）", padding=10
        )
        rotation_frame.pack(fill="x", padx=18, pady=6)
        ttk.Label(rotation_frame, text="角度（度，非负）：").grid(row=0, column=0)
        ttk.Entry(rotation_frame, textvariable=self.rotation_var, width=12).grid(
            row=0, column=1, padx=8
        )
        ttk.Combobox(
            rotation_frame, textvariable=self.rotation_direction,
            values=("顺时针", "逆时针"), state="readonly", width=10
        ).grid(row=0, column=2, padx=8)
        ttk.Label(
            rotation_frame,
            text="观察方向：从法兰 Z+ 端朝原点看。每次均相对输入姿态计算，不累加。"
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))

        # ====================================================
        # 操作
        # ====================================================
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame,
            text="计算 Rxyz",
            command=self.calculate
        ).pack(side="left", padx=8)

        ttk.Button(
            button_frame,
            text="清空",
            command=self.clear
        ).pack(side="left", padx=8)

        # ====================================================
        # 结果
        # ====================================================
        result_frame = ttk.LabelFrame(
            self.root,
            text="2. 计算结果",
            padding=10
        )
        result_frame.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=6
        )

        self.result_text = tk.Text(
            result_frame,
            font=("Consolas", 11),
            wrap="none"
        )
        self.result_text.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar = ttk.Scrollbar(
            result_frame,
            orient="vertical",
            command=self.result_text.yview
        )
        scrollbar.pack(side="right", fill="y")

        self.result_text.configure(
            yscrollcommand=scrollbar.set
        )

        ttk.Label(
            self.root,
            text=(
                "注意：仅一个 Z+ 方向不能唯一确定 Rxyz；"
                "必须再规定 X+/Y+ 的滚转方向。"
            ),
            font=("Microsoft YaHei UI", 9)
        ).pack(pady=(3, 12))

    def _build_axis_row(self, parent, title, vars_, row):
        ttk.Label(
            parent,
            text=title,
            width=18,
            font=("Microsoft YaHei UI", 10, "bold")
        ).grid(
            row=row,
            column=0,
            padx=(4, 10),
            pady=5,
            sticky="w"
        )

        for i, (axis_name, var) in enumerate(
            zip(["X", "Y", "Z"], vars_)
        ):
            ttk.Label(
                parent,
                text=axis_name
            ).grid(
                row=row,
                column=1 + i * 2,
                padx=(3, 4)
            )

            ttk.Entry(
                parent,
                textvariable=var,
                width=12,
                justify="center"
            ).grid(
                row=row,
                column=2 + i * 2,
                padx=(0, 12)
            )

    def _update_mode(self):
        if self.mode.get() == "full":
            self.zx_frame.pack_forget()
            self.full_frame.pack(
                fill="x",
                padx=18,
                pady=6,
                before=self._find_widget("快速测试")
            )
        else:
            self.full_frame.pack_forget()
            self.zx_frame.pack(
                fill="x",
                padx=18,
                pady=6,
                before=self._find_widget("快速测试")
            )

    def _find_widget(self, text):
        # 简单返回当前界面中的第一个 LabelFrame，
        # 这里只用于控制布局；找不到时返回 self
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                if widget.cget("text") == text:
                    return widget
        return self.root

    def _set_axis(self, vars_, x, y, z):
        vars_[0].set(str(x))
        vars_[1].set(str(y))
        vars_[2].set(str(z))

    def preset_current(self):
        self._set_axis(self.z_vars, 0, -1, 0)
        self._set_axis(self.x_vars, 1, 0, 0)
        self._set_axis(self.y_vars, 0, 0, 1)
        self.mode.set("full")
        self._update_mode()
        self.calculate()

    def preset_z(self, x, y, z):
        self._set_axis(self.z_vars, x, y, z)

        # 根据 Z+ 自动寻找一个简单的 X+参考方向
        if abs(x) < 0.9:
            self._set_axis(self.x_vars, 1, 0, 0)
        else:
            self._set_axis(self.x_vars, 0, 1, 0)

        self.mode.set("zx")
        self._update_mode()
        self.calculate()

    def _read_vec(self, vars_, name):
        try:
            values = [
                float(var.get().strip())
                for var in vars_
            ]
        except (ValueError, AttributeError):
            raise ValueError(
                "%s 的三个分量必须全部是数字。" % name
            )

        if not all(math.isfinite(v) for v in values):
            raise ValueError(
                "%s 不能包含 NaN 或无穷值。" % name
            )

        return tuple(values)

    def calculate(self):
        try:
            if self.mode.get() == "full":
                x_axis = self._read_vec(self.x_vars, "X+")
                y_axis = self._read_vec(self.y_vars, "Y+")
                z_axis = self._read_vec(self.z_vars, "Z+")
                rx, ry, rz, pose = axis_to_rxyz(x_axis, y_axis, z_axis)
                mode_text = "完整坐标轴模式：直接使用输入的 X+/Y+/Z+"
            else:
                z_axis = self._read_vec(self.z_vars, "Z+")
                x_ref = self._read_vec(self.x_vars, "X+参考")
                rx, ry, rz, pose = z_and_x_reference_to_rxyz(z_axis, x_ref)
                x_axis = (pose[0,0], pose[1,0], pose[2,0])
                y_axis = (pose[0,1], pose[1,1], pose[2,1])
                z_axis = (pose[0,2], pose[1,2], pose[2,2])
                mode_text = "Z+ + X+参考模式：X+参考已投影到垂直 Z+ 的平面"

            # 处理旋转角度
            angle_deg = float(self.rotation_var.get().strip())
            if not math.isfinite(angle_deg) or angle_deg < 0:
                raise ValueError("旋转角度必须是非负有限数字。")
            signed_angle = -angle_deg if self.rotation_direction.get() == "顺时针" else angle_deg
            rx, ry, rz, pose = rotate_flange_z(pose, signed_angle)

            # 提取旋转后的轴向量
            x_axis = (pose[0,0], pose[1,0], pose[2,0])
            y_axis = (pose[0,1], pose[1,1], pose[2,1])
            z_axis = (pose[0,2], pose[1,2], pose[2,2])

            # ===== 新增：回填姿态到输入框，实现连续累加 =====
            self._set_axis(self.x_vars, x_axis[0], x_axis[1], x_axis[2])
            self._set_axis(self.y_vars, y_axis[0], y_axis[1], y_axis[2])
            self._set_axis(self.z_vars, z_axis[0], z_axis[1], z_axis[2])
            # 切换模式到“完整坐标轴模式”，以便显示三个轴
            self.mode.set("full")
            self._update_mode()
            # ===================================================

            mode_text += (
                "\n追加旋转：%s %.6f°（从 Z+ 端朝原点看）"
                "\n绕法兰局部 Z 轴，右手角度 = %+.6f°"
                % (self.rotation_direction.get(), angle_deg, signed_angle)
            )

            result = (
                "========================================\n"
                "CR5 法兰坐标系 → RoboDK Rxyz\n"
                "========================================\n\n"
                "【计算模式】\n"
                "%s\n\n"
                "【最终法兰坐标轴（世界坐标）】\n"
                "X+ = (%+.6f, %+.6f, %+.6f)\n"
                "Y+ = (%+.6f, %+.6f, %+.6f)\n"
                "Z+ = (%+.6f, %+.6f, %+.6f)\n\n"
                "【旋转矩阵 R】\n"
                "[ %+.6f  %+.6f  %+.6f ]\n"
                "[ %+.6f  %+.6f  %+.6f ]\n"
                "[ %+.6f  %+.6f  %+.6f ]\n\n"
                "【RoboDK Fanuc/Motoman】\n"
                "Rx = %+.6f deg\n"
                "Ry = %+.6f deg\n"
                "Rz = %+.6f deg\n\n"
                "【可直接用于 RoboDK 的位姿】\n"
                "[0, 0, 0, %.6f, %.6f, %.6f]\n\n"
                "【轴方向说明】\n"
                "红色箭头 = X+\n"
                "绿色箭头 = Y+\n"
                "蓝色箭头 = Z+\n\n"
                "注意：\n"
                "这里的 Z+ 就是你图片中确认的法兰蓝色箭头。\n"
                "因此不再对输入 Z+ 取反。\n"
                % (
                    mode_text,
                    x_axis[0], x_axis[1], x_axis[2],
                    y_axis[0], y_axis[1], y_axis[2],
                    z_axis[0], z_axis[1], z_axis[2],
                    pose[0,0], pose[0,1], pose[0,2],
                    pose[1,0], pose[1,1], pose[1,2],
                    pose[2,0], pose[2,1], pose[2,2],
                    rx, ry, rz,
                    rx, ry, rz
                )
            )

            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", result)

        except Exception as e:
            messagebox.showerror("计算失败", "%s: %s" % (type(e).__name__, e))

    def clear(self):
        self.rotation_var.set("0")
        self.rotation_direction.set("顺时针")
        for var in (
            self.x_vars +
            self.y_vars +
            self.z_vars
        ):
            var.set("")

        self.result_text.delete("1.0", tk.END)


def main():
    root = tk.Tk()

    DirectionToRxyzGUI(root)

    root.mainloop()


if __name__ == "__main__":
    main()
