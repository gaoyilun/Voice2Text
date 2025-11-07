import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import queue
from main import process_audio_to_text
from audio_processor import AudioProcessor

class VoiceToTextGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("语音文件转文字工具")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 设置中文字体
        self.font_config = {
            'default': ('SimHei', 10),
            'title': ('SimHei', 16, 'bold'),
            'label': ('SimHei', 10, 'bold')
        }
        
        # 创建任务队列
        self.task_queue = queue.Queue()
        
        # 初始化变量
        self.input_file_path = tk.StringVar()
        self.output_file_path = tk.StringVar()
        self.engine_model = tk.StringVar(value="16k_zh")
        self.processing = False
        # 新增选项变量
        self.show_timestamp = tk.BooleanVar(value=True)  # 默认显示时间戳
        self.speaker_diarization = tk.BooleanVar(value=False)  # 默认不进行说话人分离
        self.speaker_count = tk.IntVar(value=2)  # 默认说话人数量
        # 腾讯云API密钥
        self.tenant_id = tk.StringVar()
        self.app_id = tk.StringVar()
        self.secret_id = tk.StringVar()
        self.secret_key = tk.StringVar()
        # 加载.env中的配置
        self.load_env_config()
        
        # 创建界面组件
        self.create_widgets()
        
    def get_config_path(self):
        """获取配置文件路径，兼容打包和未打包状态"""
        import sys
        # 判断是否为打包后的exe文件
        if getattr(sys, 'frozen', False):
            # 打包后，使用exe所在目录
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            # 未打包，使用脚本所在目录
            exe_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(exe_dir, '.env')
    
    def load_env_config(self):
        """从.env文件加载腾讯云配置"""
        env_path = self.get_config_path()
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key == 'TENCENTCLOUD_TENANT_ID':
                                self.tenant_id.set(value)
                            elif key == 'TENCENTCLOUD_APP_ID':
                                self.app_id.set(value)
                            elif key == 'TENCENTCLOUD_SECRET_ID':
                                self.secret_id.set(value)
                            elif key == 'TENCENTCLOUD_SECRET_KEY':
                                self.secret_key.set(value)
            except Exception as e:
                print(f"加载.env配置失败: {str(e)}")
    
    def save_env_config(self):
        """保存腾讯云配置到.env文件"""
        env_path = self.get_config_path()
        config_lines = []
        
        # 读取现有配置
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '=' in line:
                            key = line.split('=', 1)[0].strip()
                            # 跳过要更新的配置
                            if key not in ['TENCENTCLOUD_TENANT_ID', 'TENCENTCLOUD_APP_ID', 
                                          'TENCENTCLOUD_SECRET_ID', 'TENCENTCLOUD_SECRET_KEY']:
                                config_lines.append(line)
            except Exception:
                pass
        
        # 添加新配置
        config_lines.append(f'TENCENTCLOUD_TENANT_ID={self.tenant_id.get()}\n')
        config_lines.append(f'TENCENTCLOUD_APP_ID={self.app_id.get()}\n')
        config_lines.append(f'TENCENTCLOUD_SECRET_ID={self.secret_id.get()}\n')
        config_lines.append(f'TENCENTCLOUD_SECRET_KEY={self.secret_key.get()}\n')
        
        # 保存到文件
        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(config_lines)
            return True
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
            return False
    
    def open_api_settings(self):
        """打开API设置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("腾讯云API设置")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.grab_set()  # 模态窗口
        
        # 创建设置框架
        settings_frame = ttk.Frame(dialog, padding="20")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # 租户ID
        ttk.Label(settings_frame, text="租户ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(settings_frame, textvariable=self.tenant_id, width=40).grid(row=0, column=1, pady=5)
        
        # AppID
        ttk.Label(settings_frame, text="AppID:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(settings_frame, textvariable=self.app_id, width=40).grid(row=1, column=1, pady=5)
        
        # SecretID
        ttk.Label(settings_frame, text="SecretID:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(settings_frame, textvariable=self.secret_id, width=40).grid(row=2, column=1, pady=5)
        
        # SecretKey
        ttk.Label(settings_frame, text="SecretKey:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(settings_frame, textvariable=self.secret_key, width=40, show="*").grid(row=3, column=1, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="保存", command=lambda: self.save_api_settings(dialog)).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def save_api_settings(self, dialog):
        """保存API设置"""
        if self.save_env_config():
            messagebox.showinfo("成功", "API设置已保存")
            dialog.destroy()
        else:
            messagebox.showerror("错误", "保存设置失败")
    
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="语音文件转文字工具", font=self.font_config['title'])
        title_label.pack(pady=10)
        
        # API设置按钮
        ttk.Button(main_frame, text="API设置", command=self.open_api_settings).pack(side=tk.RIGHT, pady=5)
        
        # 输入文件选择
        input_frame = ttk.LabelFrame(main_frame, text="输入文件", padding="10")
        input_frame.pack(fill=tk.X, pady=10)
        
        ttk.Entry(input_frame, textvariable=self.input_file_path, width=70).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(input_frame, text="浏览", command=self.browse_input_file).pack(side=tk.RIGHT, padx=5)
        
        # 输出文件选择
        output_frame = ttk.LabelFrame(main_frame, text="输出文件", padding="10")
        output_frame.pack(fill=tk.X, pady=10)
        
        ttk.Entry(output_frame, textvariable=self.output_file_path, width=70).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="浏览", command=self.browse_output_file).pack(side=tk.RIGHT, padx=5)
        
        # 引擎模型选择
        model_frame = ttk.LabelFrame(main_frame, text="识别引擎", padding="10")
        model_frame.pack(fill=tk.X, pady=10)
        
        models = [
            ("16k_zh", "中文普通话-16k"),
            ("16k_zh_video", "中文普通话-16k-视频"),
            ("16k_en", "英语-16k"),
            ("16k_ca", "粤语-16k"),
            ("16k_ja", "日语-16k"),
            ("16k_ko", "韩语-16k")
        ]
        
        model_combo = ttk.Combobox(model_frame, textvariable=self.engine_model, values=[model[0] for model in models], width=20)
        model_combo.pack(side=tk.LEFT, padx=5)
        
        # 显示模型说明
        model_desc = ttk.Label(model_frame, text="选择语音识别模型")
        model_desc.pack(side=tk.LEFT, padx=10)
        
        # 高级选项
        advanced_frame = ttk.LabelFrame(main_frame, text="高级选项", padding="10")
        advanced_frame.pack(fill=tk.X, pady=10)
        
        # 时间戳选项
        timestamp_frame = ttk.Frame(advanced_frame)
        timestamp_frame.pack(fill=tk.X, pady=5)
        ttk.Checkbutton(timestamp_frame, text="显示时间戳", variable=self.show_timestamp).pack(side=tk.LEFT, padx=5)
        
        # 说话人分离选项
        speaker_frame = ttk.Frame(advanced_frame)
        speaker_frame.pack(fill=tk.X, pady=5)
        
        ttk.Checkbutton(speaker_frame, text="说话人分离", variable=self.speaker_diarization, 
                        command=self.toggle_speaker_count).pack(side=tk.LEFT, padx=5)
        
        self.speaker_count_frame = ttk.Frame(speaker_frame)
        self.speaker_count_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(self.speaker_count_frame, text="说话人数量:").pack(side=tk.LEFT, padx=5)
        
        # 创建说话人数量选择框
        speaker_count_values = [str(i) for i in range(1, 11)]
        self.speaker_count_combo = ttk.Combobox(self.speaker_count_frame, textvariable=self.speaker_count, 
                                              values=speaker_count_values, width=5, state=tk.DISABLED)
        self.speaker_count_combo.pack(side=tk.LEFT, padx=5)
        
        # 初始状态
        self.toggle_speaker_count()
        
        # 处理按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        self.process_button = ttk.Button(button_frame, text="开始转换", command=self.start_processing)
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(button_frame, text="取消", command=self.cancel_processing, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=10)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.pack(pady=5)
        
        # 结果展示区域
        result_frame = ttk.LabelFrame(main_frame, text="识别结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 结果文本框
        self.result_text = tk.Text(result_frame, wrap=tk.WORD, font=self.font_config['default'])
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        self.result_text.config(yscrollcommand=scrollbar.set)
        
        # 复制按钮
        ttk.Button(result_frame, text="复制结果", command=self.copy_result).pack(side=tk.BOTTOM, pady=5)
    
    def toggle_speaker_count(self):
        """根据说话人分离选项启用或禁用说话人数量选择"""
        if self.speaker_diarization.get():
            self.speaker_count_combo.config(state=tk.NORMAL)
        else:
            self.speaker_count_combo.config(state=tk.DISABLED)
        
    def browse_input_file(self):
        file_path = filedialog.askopenfilename(
            title="选择音频文件",
            filetypes=[("音频文件", "*.wav *.mp3 *.aac *.m4a *.flac *.ogg"), ("所有文件", "*.*")]
        )
        if file_path:
            self.input_file_path.set(file_path)
            # 自动建议输出文件名
            base_name = os.path.splitext(file_path)[0]
            self.output_file_path.set(f"{base_name}_transcript.txt")
    
    def browse_output_file(self):
        file_path = filedialog.asksaveasfilename(
            title="保存识别结果",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            self.output_file_path.set(file_path)
    
    def start_processing(self):
        # 验证API密钥是否已配置（租户ID非必填）
        if not self.app_id.get() or not self.secret_id.get() or not self.secret_key.get():
            messagebox.showerror("错误", "请先配置腾讯云API密钥（AppID、SecretID和SecretKey为必填项）")
            # 自动打开API设置窗口
            self.open_api_settings()
            return
        
        input_file = self.input_file_path.get()
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("错误", "请选择有效的输入文件")
            return
        
        # 检查文件格式
        if not AudioProcessor.is_supported_format(input_file):
            messagebox.showerror("错误", "不支持的音频格式")
            return
        
        # 准备处理
        self.processing = True
        self.process_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.status_var.set("正在处理...")
        self.progress_var.set(0)
        self.result_text.delete(1.0, tk.END)
        
        # 在新线程中处理，避免界面卡顿
        thread = threading.Thread(target=self.process_audio, daemon=True)
        thread.start()
        
        # 检查处理是否完成
        self.root.after(100, self.check_processing)
    
    def process_audio(self):
        try:
            input_file = self.input_file_path.get()
            output_file = self.output_file_path.get() or None
            engine_model = self.engine_model.get()
            remove_timestamp = not self.show_timestamp.get()  # 转换逻辑：show_timestamp为True时不移除
            speaker_diarization = self.speaker_diarization.get()
            speaker_count = self.speaker_count.get()
            
            # 更新进度
            self.update_status("正在验证音频文件...")
            self.update_progress(10)
            
            # 调用主程序进行处理，传入所有参数
            success = process_audio_to_text(input_file, output_file, engine_model_type=engine_model,
                                           remove_timestamp=remove_timestamp,
                                           speaker_diarization=speaker_diarization,
                                           speaker_count=speaker_count,
                                           tenant_id=self.tenant_id.get(),
                                           secret_id=self.secret_id.get(),
                                           secret_key=self.secret_key.get(),
                                           app_id=self.app_id.get())
            
            # 将结果放入队列
            self.task_queue.put((success, output_file))
        except Exception as e:
            self.task_queue.put((False, str(e)))
    
    def check_processing(self):
        if not self.processing:
            return
        
        # 检查队列中是否有结果
        try:
            success, result = self.task_queue.get(block=False)
            self.processing = False
            
            if success:
                self.update_status("转换完成")
                self.update_progress(100)
                
                # 显示结果
                if result and os.path.exists(result):
                    try:
                        with open(result, 'r', encoding='utf-8') as f:
                            content = f.read()
                            self.result_text.delete(1.0, tk.END)
                            self.result_text.insert(tk.END, content)
                    except Exception as e:
                        messagebox.showerror("错误", f"无法读取结果文件: {str(e)}")
                else:
                    messagebox.showinfo("成功", "转换成功，但未找到结果文件")
            else:
                self.update_status("转换失败")
                messagebox.showerror("错误", f"转换失败: {result}")
            
            # 重置按钮状态
            self.process_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
            
        except queue.Empty:
            # 继续检查
            self.root.after(100, self.check_processing)
    
    def cancel_processing(self):
        if messagebox.askyesno("确认", "确定要取消处理吗？"):
            self.processing = False
            self.status_var.set("已取消")
            self.process_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
    
    def update_status(self, status):
        self.status_var.set(status)
        self.root.update_idletasks()
    
    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update_idletasks()
    
    def copy_result(self):
        content = self.result_text.get(1.0, tk.END)
        if content.strip():
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            messagebox.showinfo("成功", "结果已复制到剪贴板")
        else:
            messagebox.showinfo("提示", "没有可复制的内容")

def main():
    root = tk.Tk()
    app = VoiceToTextGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()