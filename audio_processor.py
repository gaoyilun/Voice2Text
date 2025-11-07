import os
import wave
import struct
import math

class AudioProcessor:
    """音频处理类，用于处理音频文件的验证、转换和分割"""
    
    # 支持的音频格式
    SUPPORTED_FORMATS = ['.wav', '.mp3', '.aac', '.m4a', '.flac', '.ogg']
    
    # ASR服务限制
    MAX_AUDIO_DURATION = 300  # 5分钟，根据腾讯云API限制
    
    @staticmethod
    def is_supported_format(file_path):
        """检查文件格式是否支持"""
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in AudioProcessor.SUPPORTED_FORMATS
    
    @staticmethod
    def get_audio_info(file_path):
        """获取音频文件基本信息（简化版，仅处理WAV格式）"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # 对于WAV文件，尝试使用wave模块获取详细信息
            if file_ext == '.wav':
                with wave.open(file_path, 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration = frames / rate if rate > 0 else 0
                    
                    return {
                        'duration': duration,
                        'sample_rate': rate,
                        'channels': wf.getnchannels(),
                        'file_size': os.path.getsize(file_path) / (1024 * 1024)  # MB
                    }
            else:
                # 对于其他格式，只返回文件大小和估计的时长
                # 注意：这里无法准确获取非WAV格式的时长，需要用户确认
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                # 简单估计：假设1分钟约5MB（这只是一个粗略的估计）
                estimated_duration = min(file_size * 12, 3600)  # 最多估计1小时
                
                return {
                    'duration': estimated_duration,
                    'sample_rate': 0,  # 未知
                    'channels': 0,  # 未知
                    'file_size': file_size
                }
        except Exception as e:
            print(f"获取音频信息失败: {str(e)}")
            # 返回基本信息，只包含文件大小
            return {
                'duration': 0,  # 未知
                'sample_rate': 0,  # 未知
                'channels': 0,  # 未知
                'file_size': os.path.getsize(file_path) / (1024 * 1024)  # MB
            }
    
    @staticmethod
    def validate_for_asr(file_path):
        """验证音频文件是否符合ASR服务要求"""
        # 检查文件格式
        if not AudioProcessor.is_supported_format(file_path):
            return False, f"不支持的音频格式: {os.path.splitext(file_path)[1]}"
        
        # 获取音频信息（简化版）
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        
        # 检查文件大小（假设限制100MB）
        if file_size > 100:
            return False, f"文件大小超过限制（当前: {file_size:.2f}MB，限制: 100MB）"
        
        # 注意：由于没有音频库，无法准确验证时长
        # 这里简化处理，假设文件可能过长，需要分割
        # 对于非WAV文件，建议用户自行确保时长合适
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext != '.wav':
            return True, "已验证文件格式和大小，但无法准确验证时长，建议音频时长不超过5分钟"
        
        # 尝试获取WAV文件时长
        try:
            with wave.open(file_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    duration = frames / rate
                    if duration > AudioProcessor.MAX_AUDIO_DURATION:
                        return False, f"音频时长超过限制（当前: {duration:.2f}秒，限制: {AudioProcessor.MAX_AUDIO_DURATION}秒）"
        except:
            # 如果无法获取时长，返回警告但不阻止处理
            return True, "已验证文件格式和大小，但无法准确验证时长，建议音频时长不超过5分钟"
        
        return True, "验证通过"
    
    @staticmethod
    def split_large_audio(file_path):
        """简化版分割功能提示
        
        注意：由于没有音频处理库，无法实际分割文件
        这里返回提示信息，建议用户手动分割
        """
        print(f"提示: 由于环境限制，无法自动分割大文件。请手动将'{file_path}'分割为不超过5分钟的片段。")
        return []