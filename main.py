import os
import time
import json
import argparse
from tencent_cloud_api import TencentCloudAPI
from audio_processor import AudioProcessor

def process_audio_to_text(audio_file_path, output_file=None, engine_model_type="16k_zh", remove_timestamp=True, speaker_diarization=False, speaker_count=2, tenant_id=None, secret_id=None, secret_key=None, app_id=None):
    """
    处理音频文件并转换为文字
    
    Args:
        audio_file_path: 音频文件路径
        output_file: 输出文件路径，None则自动生成
        engine_model_type: 引擎模型类型，支持不同的识别模型
    """
    # 检查文件是否存在
    if not os.path.exists(audio_file_path):
        print(f"错误: 文件不存在 - {audio_file_path}")
        return False
    
    # 检查文件格式是否支持
    if not AudioProcessor.is_supported_format(audio_file_path):
        print(f"错误: 不支持的音频格式 - {audio_file_path}")
        return False
    
    # 验证音频文件是否符合ASR要求
    is_valid, message = AudioProcessor.validate_for_asr(audio_file_path)
    if not is_valid:
        print(f"错误: {message}")
        
        # 尝试分割大文件
        if "时长超过限制" in message:
            print("尝试分割大音频文件...")
            segments = AudioProcessor.split_large_audio(audio_file_path)
            if segments:
                print(f"成功分割为 {len(segments)} 个文件")
                
                # 处理每个分割后的文件
                all_results = []
                for segment_path in segments:
                    print(f"处理文件: {segment_path}")
                    result = process_single_audio(segment_path, engine_model_type, remove_timestamp, speaker_diarization, speaker_count, tenant_id, secret_id, secret_key, app_id)
                    if result:
                        all_results.append(result)
                
                # 合并结果
                if all_results:
                    merged_text = "\n".join([r['text'] for r in all_results if 'text' in r])
                    
                    # 保存结果
                    save_result(merged_text, all_results, audio_file_path, output_file)
                    return True
        return False
    
    # 处理单个音频文件
    result = process_single_audio(audio_file_path, engine_model_type, remove_timestamp, speaker_diarization, speaker_count, tenant_id, secret_id, secret_key, app_id)
    if result:
        save_result(result['text'], [result], audio_file_path, output_file)
        return True
    
    return False

def process_single_audio(audio_file_path, engine_model_type, remove_timestamp=True, speaker_diarization=False, speaker_count=2, tenant_id=None, secret_id=None, secret_key=None, app_id=None):
    """处理单个音频文件
    
    Args:
        audio_file_path: 音频文件路径
        engine_model_type: 引擎模型类型
        remove_timestamp: 是否移除时间戳
        speaker_diarization: 是否进行说话人分离
        speaker_count: 说话人数量
    
    Returns:
        dict: 包含识别结果的字典
    """
    try:
        # 初始化腾讯云API
        tencent_api = TencentCloudAPI(tenant_id=tenant_id, secret_id=secret_id, secret_key=secret_key, app_id=app_id)
        
        # 转换音频格式（如果需要）
        print("正在处理音频文件...")
        # 这里简化处理，实际使用时可能需要转换
        
        # 直接上传音频文件进行识别（不使用对象存储）
        print("正在直接上传音频文件进行识别...")
        task_response = tencent_api.recognize_audio_directly(audio_file_path, engine_model_type)
        
        if not task_response or "TaskId" not in task_response:
            print("创建识别任务失败")
            return None
        
        task_id = task_response["TaskId"]
        print(f"识别任务已创建，TaskId: {task_id}")
        
        # 轮询获取识别结果
        print("正在等待识别结果...")
        max_attempts = 60  # 最多轮询60次
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            result_response = tencent_api.get_recognition_result(task_id)
            
            if result_response and "Status" in result_response:
                status = result_response["Status"]
                
                if status == 2:  # 任务成功
                    print("识别完成！")
                    # 提取文本结果
                    text = ""
                    if "Result" in result_response:
                        text = result_response["Result"]
                        # 移除时间戳
                        if remove_timestamp:
                            lines = text.split('\n')
                            clean_lines = []
                            for line in lines:
                                # 移除类似 [0:0.000,0:1.489] 这样的时间戳
                                if '[' in line and ':' in line and ',' in line and ']' in line:
                                    # 找到最后一个 ] 的位置
                                    bracket_pos = line.rfind(']')
                                    if bracket_pos > -1 and bracket_pos + 1 < len(line):
                                        clean_lines.append(line[bracket_pos + 1:].strip())
                                    else:
                                        clean_lines.append(line)
                                else:
                                    clean_lines.append(line)
                            text = '\n'.join(clean_lines)
                    elif "ResultDetail" in result_response:
                        # 处理详细结果
                        for item in result_response["ResultDetail"]:
                            if "Text" in item:
                                text += item["Text"] + "\n"
                    
                    return {
                        "task_id": task_id,
                        "text": text,
                        "full_result": result_response
                    }
                elif status == 3:  # 任务失败
                    print(f"识别失败: {result_response.get('ErrorMsg', '未知错误')}")
                    return None
                elif status == 1:  # 任务进行中
                    print(f"识别中... (尝试 {attempt}/{max_attempts})")
                    time.sleep(3)  # 每3秒轮询一次
                elif status == 0:  # 任务等待中
                    print(f"识别等待中... (尝试 {attempt}/{max_attempts})")
                    time.sleep(3)  # 每3秒轮询一次
                else:
                    print(f"未知状态: {status}")
                    time.sleep(3)  # 未知状态也继续尝试轮询
            else:
                print("获取结果失败，重试中...")
                time.sleep(3)
        
        print("轮询超时")
        return None
    
    except Exception as e:
        print(f"处理音频文件时出错: {str(e)}")
        return None

def save_result(text, detailed_results, audio_file_path, output_file=None):
    """保存识别结果"""
    # 如果没有指定输出文件，自动生成
    if output_file is None:
        base_name = os.path.splitext(audio_file_path)[0]
        output_file = f"{base_name}_transcript.txt"
    
    # 保存文本结果
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"识别结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"保存结果时出错: {str(e)}")

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='语音文件转文字工具')
    parser.add_argument('input_file', help='输入音频文件路径')
    parser.add_argument('-o', '--output', help='输出文本文件路径（可选）')
    parser.add_argument('-m', '--model', default='16k_zh', help='引擎模型类型（默认: 16k_zh，支持其他模型如16k_en等）')
    
    args = parser.parse_args()
    
    # 显示欢迎信息
    print("=== 语音文件转文字工具 ===")
    print(f"输入文件: {args.input_file}")
    print(f"引擎模型: {args.model}")
    print("支持的模型包括: 16k_zh（中文普通话）, 16k_en（英语）等")
    print("注意: 当前使用直接上传音频文件的方式进行识别，无需对象存储服务")
    
    # 处理音频文件
    success = process_audio_to_text(args.input_file, args.output, args.model)
    
    if success:
        print("\n转换完成！")
    else:
        print("\n转换失败，请检查错误信息")

if __name__ == "__main__":
    main()