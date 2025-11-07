import os
import time
import base64
import json
from dotenv import load_dotenv
# 使用腾讯云官方SDK
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.asr.v20190614 import asr_client, models

# 加载环境变量
load_dotenv()

class TencentCloudAPI:
    def __init__(self, tenant_id=None, secret_id=None, secret_key=None, app_id=None):
        # 从参数、环境变量获取API密钥
        self.tenant_id = tenant_id or os.getenv('TENCENTCLOUD_TENANT_ID')
        self.secret_id = secret_id or os.getenv('TENCENTCLOUD_SECRET_ID')
        self.secret_key = secret_key or os.getenv('TENCENTCLOUD_SECRET_KEY')
        self.app_id = app_id or os.getenv('TENCENTCLOUD_APP_ID')
        self.region = "ap-guangzhou"
        
        # 租户ID非必填，其他为必填
        if not self.secret_id or not self.secret_key or not self.app_id:
            raise ValueError("请配置腾讯云API密钥信息（AppID、SecretID和SecretKey为必填项）")
        
        # 初始化凭证
        self.cred = credential.Credential(self.secret_id, self.secret_key)
        
        # 初始化HTTP配置
        self.http_profile = HttpProfile()
        self.http_profile.endpoint = "asr.tencentcloudapi.com"
        
        # 初始化客户端配置
        self.client_profile = ClientProfile()
        self.client_profile.httpProfile = self.http_profile
        
        # 初始化ASR客户端
        self.client = asr_client.AsrClient(self.cred, self.region, self.client_profile)
    
    def upload_audio_to_cos(self, file_path):
        """
        上传音频文件到腾讯云COS（保留此方法以兼容现有代码）
        现在此方法仅用于读取本地文件并返回base64编码
        """
        try:
            with open(file_path, 'rb') as f:
                audio_data = f.read()
                return base64.b64encode(audio_data).decode('utf-8')
        except Exception as e:
            raise Exception(f"读取音频文件失败: {str(e)}")
    
    def recognize_audio_directly(self, audio_file_path, engine_model_type="16k_zh", callback_url=""):
        """
        使用腾讯云SDK直接识别音频文件（用于长音频）
        返回任务ID信息
        """
        try:
            print(f"开始处理音频文件: {audio_file_path}")
            
            # 读取音频文件并转换为base64
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            print(f"音频文件大小: {len(audio_data)} 字节")
            
            # 创建请求对象
            req = models.CreateRecTaskRequest()
            
            # 设置请求参数
            req.EngineModelType = engine_model_type
            req.ChannelNum = 1
            req.ResTextFormat = 0
            req.SourceType = 1
            req.Data = audio_base64
            req.DataLen = len(audio_data)
            
            if callback_url:
                req.CallbackUrl = callback_url
            
            print(f"请求参数已设置，准备发送请求")
            print(f"引擎模型: {engine_model_type}")
            
            # 发送请求并获取响应
            resp = self.client.CreateRecTask(req)
            
            # 返回任务信息（将SDK响应转换为字典格式）
            response_dict = json.loads(resp.to_json_string())
            print(f"完整API响应结构: {response_dict}")
            print(f"响应类型: {type(response_dict)}")
            
            # 直接返回Data部分内容，因为API返回格式显示TaskId在Data中
            if "Data" in response_dict:
                print(f"返回Data部分: {response_dict['Data']}")
                return response_dict['Data']
            
            # 尝试其他可能的结构
            if "Response" in response_dict and "Data" in response_dict["Response"]:
                print(f"返回Response.Data部分: {response_dict['Response']['Data']}")
                return response_dict["Response"]["Data"]
            
            print("返回整个响应")
            return response_dict
            
        except Exception as e:
            print(f"识别过程中发生异常: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def recognize_audio_file(self, file_path, audio_format="wav", sample_rate=16000):
        """
        使用腾讯云SDK识别音频文件内容
        """
        try:
            # 读取音频文件并转换为base64
            with open(file_path, 'rb') as f:
                audio_data = f.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # 创建请求对象
            req = models.SentenceRecognitionRequest()
            
            # 设置请求参数
            req.EngineModelType = "16k_zh"
            req.ChannelNum = 1
            req.ResTextFormat = 0
            req.SourceType = 1
            req.Data = audio_base64
            
            # 发送请求并获取响应
            resp = self.client.SentenceRecognition(req)
            
            # 返回识别结果（将SDK响应转换为字典格式）
            return json.loads(resp.to_json_string())
            
        except Exception as e:
            raise Exception(f"语音识别失败: {str(e)}")
    
    def poll_recognition_result(self, task_id, max_retries=60, interval=5):
        """
        轮询获取语音识别结果
        """
        for retry in range(max_retries):
            try:
                result = self.get_recognition_result(task_id)
                if result.get("Response", {}).get("Status", 0) == 2:
                    # 任务完成
                    return result
                elif result.get("Response", {}).get("Status", 0) == 3:
                    # 任务失败
                    raise Exception(f"语音识别任务失败: {result.get('Response', {}).get('ErrorMsg', '未知错误')}")
                # 任务仍在进行中，继续轮询
                time.sleep(interval)
            except Exception as e:
                # 如果是API错误，直接抛出
                if "获取识别结果失败" in str(e):
                    raise
                # 其他错误，记录并重试
                print(f"轮询错误 (尝试 {retry + 1}/{max_retries}): {str(e)}")
                time.sleep(interval)
        
        # 超时
        raise Exception(f"语音识别任务超时，任务ID: {task_id}")
    
    def get_recognition_result(self, task_id):
        """
        使用腾讯云SDK获取语音识别结果（用于长音频）
        """
        try:
            print(f"正在查询任务ID: {task_id} 的识别结果")
            
            # 创建请求对象
            req = models.DescribeTaskStatusRequest()
            
            # 设置请求参数
            req.TaskId = task_id
            
            # 发送请求并获取响应
            resp = self.client.DescribeTaskStatus(req)
            
            # 转换响应为字典
            response_dict = json.loads(resp.to_json_string())
            print(f"原始API响应: {response_dict}")
            
            # 提取Data部分数据，因为main.py期望Status等字段在顶层
            result_data = {}
            
            # 处理可能的嵌套结构
            if "Response" in response_dict:
                response_data = response_dict["Response"]
                if "Data" in response_data:
                    # 直接使用Data中的所有字段，确保Status等字段在顶层
                    result_data = response_data["Data"]
                    print(f"提取Data数据到顶层: {result_data}")
                else:
                    result_data = response_data
            elif "Data" in response_dict:
                # 也可能Data直接在顶层
                result_data = response_dict["Data"]
            else:
                result_data = response_dict
            
            # 确保Status字段存在（即使是0表示未知状态）
            if "Status" not in result_data:
                result_data["Status"] = 0
                print("Status字段不存在，已添加默认值0")
            
            print(f"最终返回结果: {result_data}")
            return result_data
            
        except Exception as e:
            print(f"获取识别结果时发生异常: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"获取识别结果失败: {str(e)}")