import requests
import json
import time
import logging
from functools import wraps
from config import Config
import re

# 配置日志记录
logger = logging.getLogger(__name__)

class FeishuAPI:
    """
    飞书API处理类，负责与飞书多维表格进行交互
    """
    def __init__(self):
        self.app_id = Config.FEISHU_APP_ID
        self.app_secret = Config.FEISHU_APP_SECRET
        self.base_id = Config.BASE_ID
        self.table_id = Config.TABLE_ID
        self.access_token = None
        self.token_expire_time = 0
        
    def token_required(func):
        """
        装饰器：确保在调用API前已获取有效的访问令牌
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 检查令牌是否存在或已过期
            if not self.access_token or time.time() >= self.token_expire_time:
                self.get_access_token()
            return func(self, *args, **kwargs)
        return wrapper
    
    def get_access_token(self):
        """
        获取飞书访问令牌
        """
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            result = response.json()
            
            if result.get("code") == 0:
                self.access_token = result.get("tenant_access_token")
                # 设置令牌过期时间（提前5分钟过期，确保安全）
                self.token_expire_time = time.time() + result.get("expire") - 300
                logger.info("成功获取飞书访问令牌")
                return True
            else:
                logger.error(f"获取访问令牌失败: {result}")
                return False
        except Exception as e:
            logger.exception(f"获取访问令牌异常: {str(e)}")
            return False
    
    @token_required
    def get_records(self, page_size=100, page_token=None):
        """
        获取多维表格中的记录
        
        参数:
            page_size: 每页记录数量
            page_token: 分页标记
        
        返回:
            records: 记录列表
            has_more: 是否还有更多记录
            page_token: 下一页的标记
        """
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_id}/tables/{self.table_id}/records"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "page_size": page_size
        }
        
        if page_token:
            params["page_token"] = page_token
            
        try:
            response = requests.get(url, headers=headers, params=params)
            result = response.json()
            
            if result.get("code") == 0:
                data = result.get("data", {})
                records = data.get("items", [])
                has_more = data.get("has_more", False)
                next_page_token = data.get("page_token", None)
                
                # 处理记录数据，提取字段值
                processed_records = []
                for record in records:
                    fields = record.get("fields", {})
                    processed_record = {
                        "record_id": record.get("record_id"),
                        "title": fields.get("标题", ""),
                        "golden_sentence": clean_feishu_text(fields.get("金句输出", "")),
                        "preview": clean_feishu_text(fields.get("概要内容输出", "")),
                        "content": clean_feishu_text(fields.get("全文内容输出", "")),
                        "origin_url": extract_link(fields.get("link") or fields.get("链接", ""))
                    }
                    # 自动补全 origin_url
                    if processed_record["origin_url"] and not str(processed_record["origin_url"]).startswith(("http://", "https://")):
                        processed_record["origin_url"] = "https://" + str(processed_record["origin_url"]).lstrip('/')
                    # 若 origin_url 为空或仅为 https://，则不显示
                    if not processed_record["origin_url"] or processed_record["origin_url"] == "https://":
                        processed_record["origin_url"] = None
                    processed_records.append(processed_record)
                
                logger.info(f"成功获取记录，数量: {len(processed_records)}")
                return {
                    "records": processed_records,
                    "has_more": has_more,
                    "page_token": next_page_token
                }
            else:
                logger.error(f"获取记录失败: {result}")
                return {"records": [], "has_more": False, "page_token": None}
        except Exception as e:
            logger.exception(f"获取记录异常: {str(e)}")
            return {"records": [], "has_more": False, "page_token": None}
    
    @token_required
    def get_record_by_id(self, record_id):
        """
        根据记录ID获取单条记录详情
        
        参数:
            record_id: 记录ID
            
        返回:
            record: 记录详情
        """
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_id}/tables/{self.table_id}/records/{record_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            result = response.json()
            
            if result.get("code") == 0:
                record = result.get("data", {}).get("record", {})
                fields = record.get("fields", {})
                
                processed_record = {
                    "record_id": record.get("record_id"),
                    "title": fields.get("标题", ""),
                    "golden_sentence": clean_feishu_text(fields.get("金句输出", "")),
                    "content": clean_feishu_text(fields.get("全文内容输出", "")),
                    "origin_url": extract_link(fields.get("link") or fields.get("链接", ""))
                }
                # 自动补全 origin_url
                if processed_record["origin_url"] and not str(processed_record["origin_url"]).startswith(("http://", "https://")):
                    processed_record["origin_url"] = "https://" + str(processed_record["origin_url"]).lstrip('/')
                # 若 origin_url 为空或仅为 https://，则不显示
                if not processed_record["origin_url"] or processed_record["origin_url"] == "https://":
                    processed_record["origin_url"] = None
                logger.info(f"成功获取记录详情: {record.get('record_id')}")
                return processed_record
            else:
                logger.error(f"获取记录详情失败: {result}")
                return None
        except Exception as e:
            logger.exception(f"获取记录详情异常: {str(e)}")
            return None

def clean_feishu_text(text):
    if not text:
        return ''
    try:
        obj = json.loads(text) if isinstance(text, str) else text
        if isinstance(obj, list):
            return '\n'.join([clean_feishu_text(item) for item in obj])
        if isinstance(obj, dict):
            if 'text' in obj:
                return clean_feishu_text(obj['text'])
            return '\n'.join([clean_feishu_text(v) for v in obj.values()])
    except Exception:
        pass
    result = str(text).strip()
    # 去除开头的"文章标题：xxx"这一行
    result = re.sub(r'^文章标题：.*?(\n|$)', '', result)
    return result.strip()

def extract_link(field):
    # 兼容飞书多维表格的链接字段格式
    if isinstance(field, dict):
        return field.get("link") or field.get("text") or ""
    if isinstance(field, str):
        return field
    return ""
