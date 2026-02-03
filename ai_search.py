# coding=utf-8

"""
AI 智能搜索模块
当热搜筛选结果不足时，自动搜索相关资讯并使用 AI 筛选
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests

# 清除代理环境变量，避免代理问题
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

# 使用 requests 调用硅基流动 API（OpenAI 兼容格式）
AI_AVAILABLE = True


class AISearchManager:
    """AI 智能搜索管理器"""
    
    def __init__(self, config: Dict):
        """
        初始化 AI 搜索管理器
        
        Args:
            config: 配置字典，包含 AI_SEARCH 配置项
        """
        self.config = config
        self.ai_config = config.get("AI_SEARCH", {})
        
        # API Keys
        self.serper_api_key = self.ai_config.get("SERPER_API_KEY", "")
        self.ai_api_key = self.ai_config.get("AI_API_KEY", "")
        
        # 搜索配置（支持主关键字和备用关键字）
        self.primary_keywords = self.ai_config.get("PRIMARY_KEYWORDS", [])
        self.fallback_keywords = self.ai_config.get("FALLBACK_KEYWORDS", [])
        # 兼容旧配置：如果没有主关键字，使用 SEARCH_KEYWORDS
        if not self.primary_keywords:
            self.primary_keywords = self.ai_config.get("SEARCH_KEYWORDS", [])
        self.time_range_hours = self.ai_config.get("TIME_RANGE_HOURS", 24)
        self.max_results = self.ai_config.get("MAX_RESULTS", 30)  # 默认30条
        self.relevance_threshold = self.ai_config.get("RELEVANCE_THRESHOLD", 5)
        
        # AI 模型配置（硅基流动）
        self.ai_model_name = self.ai_config.get("AI_MODEL", "deepseek-ai/DeepSeek-V3")
        self.ai_api_base = self.ai_config.get("AI_API_BASE", "https://api.siliconflow.cn/v1")
        
        # 验证配置
        self._validate_config()
    
    def _validate_config(self):
        """验证配置是否完整"""
        if not self.serper_api_key:
            raise ValueError("未配置 SERPER_API_KEY，请在环境变量或配置文件中设置")
        
        if not self.ai_api_key:
            raise ValueError("未配置 AI_API_KEY，请在环境变量或配置文件中设置")
        
        if not self.primary_keywords and not self.fallback_keywords:
            raise ValueError("未配置搜索关键词（PRIMARY_KEYWORDS 或 FALLBACK_KEYWORDS）")
    
    def search_and_filter(self) -> List[Dict]:
        """
        执行搜索并筛选流程
        
        Returns:
            筛选后的新闻列表
        """
        try:
            print("\n" + "="*60)
            print("[AI] 智能搜索启动")
            print("="*60)
            
            # 1. 使用 Serper API 搜索
            search_results = self._search_with_serper()
            
            if not search_results:
                print("[警告] Serper 搜索未返回结果")
                return []
            
            print(f"[成功] Serper 搜索到 {len(search_results)} 条结果")
            
            # 2. 使用 AI 筛选
            filtered_results = self._filter_with_ai(search_results)
            
            # 限制推送条数，最多 15 条
            if filtered_results:
                filtered_results = filtered_results[:15]

            print(f"[成功] AI 筛选后保留 {len(filtered_results)} 条高质量新闻")
            
            # 3. 格式化为统一格式
            formatted_results = self._format_results(filtered_results)
            
            print("="*60)
            print(f"[完成] AI 搜索完成，共获取 {len(formatted_results)} 条资讯")
            print("="*60 + "\n")
            
            return formatted_results
            
        except Exception as e:
            print(f"[错误] AI 搜索出错: {e}")
            return []
    
    def _search_with_serper(self) -> List[Dict]:
        """
        使用 Serper API 搜索新闻（多轮搜索策略）
        
        策略：
        1. 优先使用主关键字（订阅关键字）搜索，目标获取30条结果
        2. 如果结果不足（< 20条），使用备用关键字补充搜索
        
        Returns:
            搜索结果列表（去重后）
        """
        all_results = []
        seen_urls = set()  # 用于去重
        
        # API 请求参数
        url = "https://google.serper.dev/news"
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json"
        }
        
        def _perform_search(query: str, round_name: str) -> List[Dict]:
            """执行单次搜索"""
            payload = {
                "q": query,
                "num": self.max_results,
                "gl": "cn",  # 地区：中国
                "hl": "zh-cn",  # 语言：中文
                "tbs": f"qdr:d"  # 时间：过去一天
            }
            
            print(f"[搜索] {round_name}: {query}")
            print(f"   搜索范围: 过去 {self.time_range_hours} 小时")
            
            # 发送请求（添加重试机制）
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # 创建 session 并禁用代理
                    session = requests.Session()
                    session.trust_env = False  # 禁用环境变量代理
                    
                    response = session.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        news_results = data.get("news", [])
                        
                        # 过滤时间范围
                        filtered_news = self._filter_by_time(news_results)
                        return filtered_news
                    
                    elif response.status_code == 429:
                        # 速率限制，等待后重试
                        wait_time = 2 ** attempt
                        print(f"   [警告] 触发速率限制，等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    
                    else:
                        print(f"   [错误] Serper API 错误: {response.status_code}")
                        print(f"   响应内容: {response.text[:200]}")
                        return []
                
                except requests.Timeout:
                    if attempt < max_retries - 1:
                        print(f"   [警告] 请求超时，重试 ({attempt + 1}/{max_retries})...")
                        time.sleep(1)
                        continue
                    else:
                        print("   [错误] 请求超时，已达到最大重试次数")
                        return []
            
            return []
        
        try:
            # 第一轮：使用主关键字搜索
            if self.primary_keywords:
                query = " OR ".join(self.primary_keywords)
                primary_results = _perform_search(query, "第一轮搜索（主关键字）")
                
                # 去重并添加到结果列表
                for news in primary_results:
                    news_url = news.get("link", "")
                    if news_url and news_url not in seen_urls:
                        seen_urls.add(news_url)
                        all_results.append(news)
                
                print(f"   [结果] 主关键字搜索获得 {len(primary_results)} 条，去重后 {len(all_results)} 条")
            
            # 第二轮：如果结果不足，使用备用关键字补充
            if len(all_results) < 20 and self.fallback_keywords:
                query = " OR ".join(self.fallback_keywords)
                fallback_results = _perform_search(query, "第二轮搜索（备用关键字）")
                
                # 去重并添加到结果列表
                added_count = 0
                for news in fallback_results:
                    news_url = news.get("link", "")
                    if news_url and news_url not in seen_urls:
                        seen_urls.add(news_url)
                        all_results.append(news)
                        added_count += 1
                
                print(f"   [结果] 备用关键字搜索获得 {len(fallback_results)} 条，新增 {added_count} 条")
            
            return all_results
            
        except Exception as e:
            print(f"[错误] Serper 搜索失败: {e}")
            return []
    
    def _filter_by_time(self, news_list: List[Dict]) -> List[Dict]:
        """
        按时间范围过滤新闻
        
        Args:
            news_list: 新闻列表
            
        Returns:
            过滤后的新闻列表
        """
        cutoff_time = datetime.now() - timedelta(hours=self.time_range_hours)
        filtered = []
        
        for news in news_list:
            try:
                # Serper 返回的时间格式：相对时间（如 "2 hours ago"）或日期
                date_str = news.get("date", "")
                
                # 简单处理：如果包含 "ago"，说明是最近的新闻
                if "ago" in date_str.lower() or "小时" in date_str or "分钟" in date_str:
                    filtered.append(news)
                # 如果是今天的新闻
                elif "today" in date_str.lower() or "今天" in date_str:
                    filtered.append(news)
                # 其他情况也保留（Serper 已经按时间筛选过了）
                else:
                    filtered.append(news)
            except Exception:
                # 解析失败也保留
                filtered.append(news)
        
        return filtered
    
    def _filter_with_ai(self, news_list: List[Dict]) -> List[Dict]:
        """
        使用硅基流动 AI（DeepSeek-V3）筛选和分析新闻
        
        Args:
            news_list: 搜索结果列表
            
        Returns:
            筛选后的高质量新闻列表
        """
        try:
            # 构建新闻摘要供 AI 分析
            news_summaries = []
            for idx, news in enumerate(news_list):
                summary = {
                    "id": idx,
                    "title": news.get("title", ""),
                    "snippet": news.get("snippet", ""),
                    "source": news.get("source", "")
                }
                news_summaries.append(summary)
            
            # 构建订阅关键字信息（用于prompt）
            keywords_info = ""
            if self.primary_keywords:
                keywords_info = f"订阅关键字: {', '.join(self.primary_keywords[:10])}"  # 只显示前10个
            
            # 构建 Prompt
            prompt = f"""你是一个专业的资讯分析专家。请分析以下新闻列表，筛选出与订阅主题强相关的高质量内容。

**订阅主题关键字：**
{keywords_info}

**重点关注内容类型：**
1. 政策相关：政策发布、政策调整、政策解读等
2. 热点新闻：行业热点、重大事件、重要动态
3. 热点话题：社会关注、讨论热点、趋势话题
4. 医疗保险相关知识：保险产品、理赔案例、保障范围等
5. 行业资讯和趋势：市场动态、发展趋势、行业分析

**评分标准（0-10分）：**
- 8-10分：与订阅主题强相关，涉及政策、热点、医疗保险、趋势等，信息价值高，必须保留
- 5-7分：中度相关，有一定参考价值，可以保留
- 0-4分：低相关或无关（如仅提及关键字但内容不相关），必须过滤掉

**重要原则：**
- 只保留与订阅主题有强关联的新闻
- 如果新闻只是简单提及关键字，但内容与主题无关，应给予低分（0-4分）并过滤
- 优先保留政策、热点、医疗保险、趋势相关的内容

**新闻列表：**
{json.dumps(news_summaries, ensure_ascii=False, indent=2)}

**要求：**
请对每条新闻评分，并返回 JSON 格式：
{{
  "filtered_news": [
    {{
      "id": 0,
      "score": 8,
      "reason": "关于养老保险政策调整的权威报道，与订阅主题强相关"
    }}
  ]
}}

只返回评分 >= {self.relevance_threshold} 的新闻。请严格筛选，确保只保留真正相关的新闻。
"""
            
            print(f"[AI] 正在调用 {self.ai_model_name} 进行智能筛选...")
            
            # 调用硅基流动 API（OpenAI 兼容格式）
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    api_url = f"{self.ai_api_base}/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {self.ai_api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": self.ai_model_name,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000
                    }
                    
                    # 发送请求
                    session = requests.Session()
                    session.trust_env = False  # 禁用环境变量代理
                    response = session.post(api_url, headers=headers, json=payload, timeout=60)
                    
                    if response.status_code != 200:
                        raise Exception(f"API 返回错误: {response.status_code}, {response.text[:200]}")
                    
                    result_data = response.json()
                    
                    # 提取响应内容
                    if "choices" in result_data and len(result_data["choices"]) > 0:
                        response_text = result_data["choices"][0]["message"]["content"].strip()
                    else:
                        raise Exception(f"API 响应格式错误: {result_data}")
                    
                    # 提取 JSON（去除可能的 markdown 代码块标记）
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0].strip()
                    
                    result = json.loads(response_text)
                    filtered_ids = [item["id"] for item in result.get("filtered_news", [])]
                    
                    # 返回筛选后的新闻
                    filtered_news = [news_list[idx] for idx in filtered_ids if idx < len(news_list)]
                    
                    # 输出筛选详情
                    print(f"   [成功] AI 分析完成，保留 {len(filtered_news)}/{len(news_list)} 条")
                    for item in result.get("filtered_news", [])[:3]:  # 显示前3条
                        print(f"      • ID {item['id']} (评分: {item['score']}/10): {item['reason']}")
                    if len(result.get("filtered_news", [])) > 3:
                        print(f"      ... 还有 {len(result.get('filtered_news', [])) - 3} 条")
                    
                    return filtered_news
                
                except json.JSONDecodeError as e:
                    if attempt < max_retries - 1:
                        print(f"   [警告] JSON 解析失败，重试 ({attempt + 1}/{max_retries})...")
                        if 'response_text' in locals():
                            print(f"   响应内容: {response_text[:200]}...")
                        time.sleep(1)
                        continue
                    else:
                        print(f"   [错误] JSON 解析失败: {e}")
                        # 降级策略：返回所有结果
                        print("   [警告] 降级策略：返回所有搜索结果")
                        return news_list
                
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"   [警告] AI 调用失败，重试 ({attempt + 1}/{max_retries})...")
                        print(f"   错误: {str(e)[:100]}")
                        time.sleep(2)
                        continue
                    else:
                        print(f"   [错误] AI 调用失败: {e}")
                        # 降级策略：返回所有结果
                        return news_list
            
            return news_list
            
        except Exception as e:
            print(f"[错误] AI 筛选失败: {e}")
            # 降级策略：返回所有结果
            return news_list
    
    def _format_results(self, news_list: List[Dict]) -> List[Dict]:
        """
        将搜索结果转换为与热搜数据一致的格式
        
        Args:
            news_list: 原始新闻列表
            
        Returns:
            格式化后的新闻列表
        """
        formatted = []
        
        for news in news_list:
            try:
                # 转换为统一格式
                formatted_item = {
                    "title": news.get("title", ""),
                    "url": news.get("link", ""),
                    "mobileUrl": news.get("link", ""),  # Serper 没有单独的移动端链接
                    "source": "AI智能搜索",
                    "platform_id": "ai_search",
                    "rank": 0,  # AI 搜索的结果没有排名
                    "ranks": [],
                    "source_type": "ai_search",
                    "original_source": news.get("source", "未知来源"),
                    "date": news.get("date", ""),
                    "snippet": news.get("snippet", "")
                }
                formatted.append(formatted_item)
            except Exception as e:
                print(f"   [警告] 格式化新闻失败: {e}")
                continue
        
        return formatted


def search_pension_news_with_ai(config: Dict) -> List[Dict]:
    """
    便捷函数：使用AI搜索相关资讯
    
    Args:
        config: 配置字典，包含 AI_SEARCH 配置项
        
    Returns:
        筛选后的资讯列表
    """
    try:
        ai_config = config.get("AI_SEARCH", {})

        
        # 检查是否启用
        if not ai_config.get("ENABLED", False):
            return []
        
        # 检查 API Keys
        if not ai_config.get("SERPER_API_KEY") or not ai_config.get("AI_API_KEY"):
            print("[警告] AI 搜索功能已启用但未配置 API Keys，跳过")
            return []
        
        # 执行搜索
        manager = AISearchManager(config)
        results = manager.search_and_filter()
        
        return results
        
    except Exception as e:
        print(f"[错误] AI 搜索出错: {e}")
        return []

