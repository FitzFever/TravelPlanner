# 旅行规划Multi-Agent系统 - 真实数据源MCP工具集成

基于真实API的MCP工具实现，获取准确的POI、地图、住宿等数据

## 🎯 MCP工具架构设计

### 核心MCP工具集
```
MCP工具生态系统
├── tavily_search_mcp     # 通用搜索 (已有)
├── amap_poi_mcp          # 高德地图POI搜索
├── gaode_route_mcp       # 高德路线规划  
├── booking_mcp           # Booking.com住宿
├── weather_mcp           # 天气查询
└── currency_mcp          # 汇率转换
```

## 📍 1. 高德地图POI搜索MCP工具

### 1.1 高德MCP服务器实现

```python
# tools/mcp_servers/amap_poi_server.py
from mcp.server import FastMCP
import aiohttp
import json
from typing import List, Dict, Any

class AmapPOIServer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3"
        self.mcp = FastMCP("AMapPOI", port=8003)
        self._setup_tools()
    
    def _setup_tools(self):
        """设置MCP工具"""
        
        @self.mcp.tool()
        async def search_pois(
            city: str,
            keywords: str, 
            poi_type: str = "",
            page_size: int = 20
        ) -> Dict[str, Any]:
            """
            搜索指定城市的POI信息
            
            Args:
                city: 城市名称，如"北京"
                keywords: 搜索关键词，如"景点"
                poi_type: POI类型代码，如"110000"(景点)
                page_size: 返回结果数量，最大50
            
            Returns:
                包含POI详细信息的字典
            """
            return await self._search_pois(city, keywords, poi_type, page_size)
        
        @self.mcp.tool()
        async def get_poi_details(poi_id: str) -> Dict[str, Any]:
            """
            获取POI详细信息
            
            Args:
                poi_id: POI的唯一标识符
                
            Returns:
                POI的详细信息
            """
            return await self._get_poi_details(poi_id)
        
        @self.mcp.tool() 
        async def search_nearby_pois(
            longitude: float,
            latitude: float,
            radius: int = 3000,
            poi_type: str = ""
        ) -> Dict[str, Any]:
            """
            搜索指定坐标附近的POI
            
            Args:
                longitude: 经度
                latitude: 纬度  
                radius: 搜索半径，单位米
                poi_type: POI类型
                
            Returns:
                附近POI列表
            """
            return await self._search_nearby_pois(longitude, latitude, radius, poi_type)
    
    async def _search_pois(self, city: str, keywords: str, poi_type: str, page_size: int) -> Dict:
        """搜索POI实现"""
        url = f"{self.base_url}/place/text"
        params = {
            "key": self.api_key,
            "keywords": keywords,
            "city": city,
            "types": poi_type,
            "page_size": page_size,
            "extensions": "all"  # 获取详细信息
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._format_poi_response(data)
                    else:
                        return {"error": f"API请求失败: {response.status}"}
            except Exception as e:
                return {"error": f"网络请求错误: {str(e)}"}
    
    async def _get_poi_details(self, poi_id: str) -> Dict:
        """获取POI详情实现"""
        url = f"{self.base_url}/place/detail"
        params = {
            "key": self.api_key,
            "id": poi_id,
            "extensions": "all"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        return {"error": f"API请求失败: {response.status}"}
            except Exception as e:
                return {"error": f"网络请求错误: {str(e)}"}
    
    async def _search_nearby_pois(self, lng: float, lat: float, radius: int, poi_type: str) -> Dict:
        """搜索附近POI实现"""
        url = f"{self.base_url}/place/around"
        params = {
            "key": self.api_key,
            "location": f"{lng},{lat}",
            "radius": radius,
            "types": poi_type,
            "extensions": "all"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._format_poi_response(data)
                    else:
                        return {"error": f"API请求失败: {response.status}"}
            except Exception as e:
                return {"error": f"网络请求错误: {str(e)}"}
    
    async def _format_poi_response(self, raw_data: Dict) -> Dict:
        """格式化POI响应数据"""
        if raw_data.get("status") != "1":
            return {"error": "高德API返回错误", "raw": raw_data}
        
        pois = raw_data.get("pois", [])
        formatted_pois = []
        
        for poi in pois:
            # 解析高德数据格式
            location_str = poi.get("location", "0,0")
            lng, lat = map(float, location_str.split(","))
            
            formatted_poi = {
                "id": poi.get("id"),
                "name": poi.get("name"),
                "type": poi.get("type"),
                "type_code": poi.get("typecode"),
                "address": poi.get("address"),
                "location": {"longitude": lng, "latitude": lat},
                "tel": poi.get("tel"),
                "rating": self._parse_rating(poi.get("biz_ext", {})),
                "business_hours": poi.get("business", {}).get("opentime", ""),
                "photos": self._extract_photos(poi.get("photos", [])),
                "description": poi.get("introduction", ""),
                "price_info": self._parse_price_info(poi.get("biz_ext", {})),
                "tags": poi.get("tag", "").split(";") if poi.get("tag") else [],
                "district": poi.get("adname"),
                "city": poi.get("cityname")
            }
            formatted_pois.append(formatted_poi)
        
        return {
            "count": len(formatted_pois),
            "pois": formatted_pois,
            "status": "success"
        }
    
    def _parse_rating(self, biz_ext: Dict) -> float:
        """解析评分信息"""
        rating_str = biz_ext.get("rating", "0")
        try:
            return float(rating_str) if rating_str else 0.0
        except:
            return 0.0
    
    def _extract_photos(self, photos: List) -> List[str]:
        """提取照片URL"""
        return [photo.get("url", "") for photo in photos if photo.get("url")]
    
    def _parse_price_info(self, biz_ext: Dict) -> Dict:
        """解析价格信息"""
        return {
            "avg_price": biz_ext.get("cost", ""),
            "price_desc": biz_ext.get("price", "")
        }
    
    def run(self):
        """启动MCP服务器"""
        self.mcp.run(transport="streamable-http")

# 启动脚本
if __name__ == "__main__":
    import os
    api_key = os.getenv("AMAP_API_KEY")
    if not api_key:
        raise ValueError("请设置AMAP_API_KEY环境变量")
    
    server = AmapPOIServer(api_key)
    server.run()
```

### 1.2 高德路线规划MCP工具

```python
# tools/mcp_servers/amap_route_server.py  
from mcp.server import FastMCP
import aiohttp
import json
from typing import List, Dict, Any, Tuple

class AmapRouteServer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3"
        self.mcp = FastMCP("AMapRoute", port=8004)
        self._setup_tools()
    
    def _setup_tools(self):
        """设置路线规划工具"""
        
        @self.mcp.tool()
        async def plan_driving_route(
            origin: str,  # "lng,lat" 格式
            destination: str,  # "lng,lat" 格式  
            waypoints: str = "",  # 途经点 "lng1,lat1;lng2,lat2"
            strategy: int = 0  # 路径策略: 0-速度优先, 1-费用优先, 2-距离优先
        ) -> Dict[str, Any]:
            """
            规划驾车路线
            
            Args:
                origin: 起点坐标 "经度,纬度"
                destination: 终点坐标 "经度,纬度"
                waypoints: 途经点坐标，多个用;分隔
                strategy: 路径策略
                
            Returns:
                包含路线详情的字典
            """
            return await self._plan_route("driving", origin, destination, waypoints, strategy)
        
        @self.mcp.tool()
        async def plan_walking_route(
            origin: str,
            destination: str
        ) -> Dict[str, Any]:
            """
            规划步行路线
            
            Args:
                origin: 起点坐标
                destination: 终点坐标
                
            Returns:
                步行路线详情
            """
            return await self._plan_route("walking", origin, destination)
        
        @self.mcp.tool()
        async def plan_transit_route(
            origin: str,
            destination: str,
            city: str,
            strategy: int = 0
        ) -> Dict[str, Any]:
            """
            规划公交路线
            
            Args:
                origin: 起点坐标
                destination: 终点坐标  
                city: 城市名称
                strategy: 公交策略 0-最快捷, 1-最经济, 2-最少换乘
                
            Returns:
                公交路线详情
            """
            return await self._plan_transit_route(origin, destination, city, strategy)
        
        @self.mcp.tool()
        async def calculate_distance_matrix(
            origins: List[str],  # 起点列表 ["lng1,lat1", "lng2,lat2"]
            destinations: List[str]  # 终点列表
        ) -> Dict[str, Any]:
            """
            批量计算距离和时间矩阵
            
            Args:
                origins: 起点坐标列表
                destinations: 终点坐标列表
                
            Returns:
                距离时间矩阵
            """
            return await self._calculate_distance_matrix(origins, destinations)
    
    async def _plan_route(self, route_type: str, origin: str, destination: str, 
                         waypoints: str = "", strategy: int = 0) -> Dict:
        """路线规划实现"""
        if route_type == "driving":
            url = f"{self.base_url}/direction/driving"
        elif route_type == "walking":
            url = f"{self.base_url}/direction/walking"
        else:
            return {"error": f"不支持的路线类型: {route_type}"}
        
        params = {
            "key": self.api_key,
            "origin": origin,
            "destination": destination,
            "extensions": "all"
        }
        
        if route_type == "driving":
            params["strategy"] = strategy
            if waypoints:
                params["waypoints"] = waypoints
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._format_route_response(data, route_type)
                    else:
                        return {"error": f"API请求失败: {response.status}"}
            except Exception as e:
                return {"error": f"网络请求错误: {str(e)}"}
    
    async def _plan_transit_route(self, origin: str, destination: str, 
                                city: str, strategy: int) -> Dict:
        """公交路线规划"""
        url = f"{self.base_url}/direction/transit/integrated"
        params = {
            "key": self.api_key,
            "origin": origin,
            "destination": destination,
            "city": city,
            "strategy": strategy,
            "extensions": "all"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._format_transit_response(data)
                    else:
                        return {"error": f"API请求失败: {response.status}"}
            except Exception as e:
                return {"error": f"网络请求错误: {str(e)}"}
    
    async def _calculate_distance_matrix(self, origins: List[str], destinations: List[str]) -> Dict:
        """距离矩阵计算"""
        url = f"{self.base_url}/distance"
        params = {
            "key": self.api_key,
            "origins": "|".join(origins),
            "destination": "|".join(destinations),
            "type": "1"  # 驾车距离
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_distance_matrix(data, origins, destinations)
                    else:
                        return {"error": f"API请求失败: {response.status}"}
            except Exception as e:
                return {"error": f"网络请求错误: {str(e)}"}
    
    async def _format_route_response(self, raw_data: Dict, route_type: str) -> Dict:
        """格式化路线响应"""
        if raw_data.get("status") != "1":
            return {"error": "高德API返回错误", "raw": raw_data}
        
        route_key = "paths" if route_type == "driving" else "paths"
        routes = raw_data.get("route", {}).get(route_key, [])
        
        if not routes:
            return {"error": "未找到路线"}
        
        # 取第一条推荐路线
        best_route = routes[0]
        
        formatted_route = {
            "distance": int(best_route.get("distance", 0)),  # 米
            "duration": int(best_route.get("duration", 0)),  # 秒
            "toll_distance": int(best_route.get("toll_distance", 0)),  # 收费路段距离
            "tolls": int(best_route.get("tolls", 0)),  # 过路费，单位：元
            "traffic_lights": int(best_route.get("traffic_lights", 0)),  # 红绿灯个数
            "steps": self._format_route_steps(best_route.get("steps", [])),
            "polyline": best_route.get("polyline", ""),  # 路线坐标点
            "route_type": route_type
        }
        
        return {
            "status": "success",
            "route": formatted_route,
            "alternative_routes": [self._format_route_basic(route) for route in routes[1:3]]  # 备选路线
        }
    
    def _format_route_steps(self, steps: List[Dict]) -> List[Dict]:
        """格式化路线步骤"""
        formatted_steps = []
        for step in steps:
            formatted_step = {
                "instruction": step.get("instruction", ""),
                "distance": int(step.get("distance", 0)),
                "duration": int(step.get("duration", 0)),
                "polyline": step.get("polyline", ""),
                "action": step.get("action", ""),
                "road_name": step.get("road", "")
            }
            formatted_steps.append(formatted_step)
        return formatted_steps
    
    def _format_route_basic(self, route: Dict) -> Dict:
        """格式化基础路线信息"""
        return {
            "distance": int(route.get("distance", 0)),
            "duration": int(route.get("duration", 0)),
            "tolls": int(route.get("tolls", 0))
        }
    
    async def _format_transit_response(self, raw_data: Dict) -> Dict:
        """格式化公交路线响应"""
        if raw_data.get("status") != "1":
            return {"error": "高德API返回错误", "raw": raw_data}
        
        transits = raw_data.get("route", {}).get("transits", [])
        
        if not transits:
            return {"error": "未找到公交路线"}
        
        formatted_transits = []
        for transit in transits:
            formatted_transit = {
                "cost": int(transit.get("cost", 0)),  # 花费时间，单位：秒
                "duration": int(transit.get("duration", 0)),
                "nightflag": transit.get("nightflag", "0"),  # 是否夜班车
                "walking_distance": int(transit.get("walking_distance", 0)),
                "segments": self._format_transit_segments(transit.get("segments", []))
            }
            formatted_transits.append(formatted_transit)
        
        return {
            "status": "success", 
            "transits": formatted_transits
        }
    
    def _format_transit_segments(self, segments: List[Dict]) -> List[Dict]:
        """格式化公交段落"""
        formatted_segments = []
        for segment in segments:
            if segment.get("walking"):
                # 步行段
                walking = segment["walking"]
                formatted_segments.append({
                    "type": "walking",
                    "distance": int(walking.get("distance", 0)),
                    "duration": int(walking.get("duration", 0)),
                    "instruction": "步行"
                })
            elif segment.get("bus"):
                # 公交段
                bus = segment["bus"]
                buslines = bus.get("buslines", [])
                for busline in buslines:
                    formatted_segments.append({
                        "type": "bus",
                        "name": busline.get("name", ""),
                        "via_num": int(busline.get("via_num", 0)),  # 经过站数
                        "duration": int(busline.get("duration", 0)),
                        "departure_stop": busline.get("departure_stop", {}).get("name", ""),
                        "arrival_stop": busline.get("arrival_stop", {}).get("name", "")
                    })
        
        return formatted_segments
    
    def _format_distance_matrix(self, raw_data: Dict, origins: List[str], destinations: List[str]) -> Dict:
        """格式化距离矩阵"""
        if raw_data.get("status") != "1":
            return {"error": "高德API返回错误", "raw": raw_data}
        
        results = raw_data.get("results", [])
        matrix = []
        
        for i, result in enumerate(results):
            row = {
                "origin_index": i,
                "origin": origins[i] if i < len(origins) else "",
                "distances": []
            }
            
            for j, dest in enumerate(destinations):
                if j < len(result):
                    distance_info = result[j]
                    row["distances"].append({
                        "destination_index": j,
                        "destination": dest,
                        "distance": int(distance_info.get("distance", 0)),
                        "duration": int(distance_info.get("duration", 0))
                    })
            
            matrix.append(row)
        
        return {
            "status": "success",
            "matrix": matrix
        }
    
    def run(self):
        """启动MCP服务器"""
        self.mcp.run(transport="streamable-http")

if __name__ == "__main__":
    import os
    api_key = os.getenv("AMAP_API_KEY") 
    if not api_key:
        raise ValueError("请设置AMAP_API_KEY环境变量")
    
    server = AmapRouteServer(api_key)
    server.run()
```

## 🏨 2. Booking.com住宿MCP工具

```python
# tools/mcp_servers/booking_mcp_server.py
from mcp.server import FastMCP
import aiohttp
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta

class BookingMCPServer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://booking-com.p.rapidapi.com/v1"
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
        }
        self.mcp = FastMCP("BookingCom", port=8005)
        self._setup_tools()
    
    def _setup_tools(self):
        """设置住宿搜索工具"""
        
        @self.mcp.tool()
        async def search_hotels(
            city: str,
            checkin_date: str,  # YYYY-MM-DD
            checkout_date: str,  # YYYY-MM-DD
            adults: int = 2,
            rooms: int = 1,
            price_min: int = 0,
            price_max: int = 9999
        ) -> Dict[str, Any]:
            """
            搜索酒店
            
            Args:
                city: 城市名称
                checkin_date: 入住日期
                checkout_date: 退房日期
                adults: 成人数量
                rooms: 房间数量
                price_min: 最低价格
                price_max: 最高价格
                
            Returns:
                酒店搜索结果
            """
            return await self._search_hotels(city, checkin_date, checkout_date, 
                                           adults, rooms, price_min, price_max)
        
        @self.mcp.tool()
        async def get_hotel_details(hotel_id: str) -> Dict[str, Any]:
            """
            获取酒店详细信息
            
            Args:
                hotel_id: 酒店ID
                
            Returns:
                酒店详细信息
            """
            return await self._get_hotel_details(hotel_id)
        
        @self.mcp.tool()
        async def search_hotels_by_location(
            latitude: float,
            longitude: float,
            checkin_date: str,
            checkout_date: str,
            radius: int = 5000,  # 搜索半径，米
            adults: int = 2
        ) -> Dict[str, Any]:
            """
            按位置搜索酒店
            
            Args:
                latitude: 纬度
                longitude: 经度
                checkin_date: 入住日期
                checkout_date: 退房日期
                radius: 搜索半径
                adults: 成人数量
                
            Returns:
                附近酒店列表
            """
            return await self._search_hotels_by_location(latitude, longitude, 
                                                       checkin_date, checkout_date, 
                                                       radius, adults)
    
    async def _search_hotels(self, city: str, checkin: str, checkout: str,
                           adults: int, rooms: int, price_min: int, price_max: int) -> Dict:
        """搜索酒店实现"""
        # 首先获取城市ID
        dest_id = await self._get_destination_id(city)
        if not dest_id:
            return {"error": f"未找到城市: {city}"}
        
        url = f"{self.base_url}/hotels/search"
        params = {
            "dest_id": dest_id,
            "dest_type": "city",
            "checkin_date": checkin,
            "checkout_date": checkout,
            "adults_number": adults,
            "room_number": rooms,
            "price_filter_currencycode": "CNY",
            "order_by": "popularity",
            "filter_by_currency": "CNY",
            "include_adjacency": "true",
            "page_number": 0,
            "units": "metric"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._format_hotel_search_response(data, price_min, price_max)
                    else:
                        return {"error": f"Booking API请求失败: {response.status}"}
            except Exception as e:
                return {"error": f"网络请求错误: {str(e)}"}
    
    async def _get_destination_id(self, city: str) -> str:
        """获取目的地ID"""
        url = f"{self.base_url}/hotels/locations"
        params = {"name": city, "locale": "zh"}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            return str(data[0].get("dest_id", ""))
                    return ""
            except Exception as e:
                print(f"获取目的地ID失败: {e}")
                return ""
    
    async def _format_hotel_search_response(self, raw_data: Dict, price_min: int, price_max: int) -> Dict:
        """格式化酒店搜索响应"""
        hotels = raw_data.get("result", [])
        
        formatted_hotels = []
        for hotel in hotels:
            # 价格过滤
            min_price = hotel.get("min_total_price", 0)
            if min_price < price_min or min_price > price_max:
                continue
            
            formatted_hotel = {
                "id": hotel.get("hotel_id"),
                "name": hotel.get("hotel_name"),
                "address": hotel.get("address"),
                "city": hotel.get("city"),
                "country": hotel.get("country_trans"),
                "latitude": hotel.get("latitude"),
                "longitude": hotel.get("longitude"),
                "rating": hotel.get("review_score", 0),
                "rating_count": hotel.get("review_nr", 0),
                "stars": hotel.get("class", 0),
                "price": {
                    "min_price": min_price,
                    "currency": hotel.get("currency_code", "CNY"),
                    "price_breakdown": hotel.get("price_breakdown", {})
                },
                "amenities": hotel.get("hotel_facilities", []),
                "photos": self._extract_hotel_photos(hotel.get("main_photo_url", "")),
                "distance_to_center": hotel.get("distance", ""),
                "accommodation_type": hotel.get("accommodation_type_name", ""),
                "booking_url": f"https://www.booking.com/hotel/{hotel.get('cc1', '').lower()}/{hotel.get('hotel_name_trans', '').replace(' ', '-').lower()}.html"
            }
            formatted_hotels.append(formatted_hotel)
        
        return {
            "status": "success",
            "count": len(formatted_hotels),
            "hotels": formatted_hotels[:20]  # 限制返回数量
        }
    
    def _extract_hotel_photos(self, main_photo_url: str) -> List[str]:
        """提取酒店照片"""
        photos = []
        if main_photo_url:
            photos.append(main_photo_url)
        return photos
    
    async def _get_hotel_details(self, hotel_id: str) -> Dict:
        """获取酒店详情"""
        url = f"{self.base_url}/hotels/details"
        params = {"hotel_id": hotel_id}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_hotel_details(data)
                    else:
                        return {"error": f"获取酒店详情失败: {response.status}"}
            except Exception as e:
                return {"error": f"网络请求错误: {str(e)}"}
    
    def _format_hotel_details(self, raw_data: Dict) -> Dict:
        """格式化酒店详情"""
        return {
            "status": "success",
            "hotel": {
                "id": raw_data.get("hotel_id"),
                "name": raw_data.get("hotel_name"),
                "description": raw_data.get("hotel_description", ""),
                "facilities": raw_data.get("hotel_facilities", []),
                "policies": raw_data.get("hotel_policies", {}),
                "room_types": raw_data.get("room_types", []),
                "photos": raw_data.get("hotel_photos", []),
                "contact": {
                    "phone": raw_data.get("phone", ""),
                    "email": raw_data.get("email", "")
                }
            }
        }
    
    async def _search_hotels_by_location(self, lat: float, lng: float, checkin: str, 
                                       checkout: str, radius: int, adults: int) -> Dict:
        """按位置搜索酒店"""
        url = f"{self.base_url}/hotels/search-by-coordinates"
        params = {
            "latitude": lat,
            "longitude": lng,
            "checkin_date": checkin,
            "checkout_date": checkout,
            "adults_number": adults,
            "radius": radius,
            "units": "metric"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._format_hotel_search_response(data, 0, 9999)
                    else:
                        return {"error": f"按位置搜索失败: {response.status}"}
            except Exception as e:
                return {"error": f"网络请求错误: {str(e)}"}
    
    def run(self):
        """启动MCP服务器"""
        self.mcp.run(transport="streamable-http")

if __name__ == "__main__":
    import os
    api_key = os.getenv("RAPIDAPI_KEY")  # RapidAPI密钥
    if not api_key:
        raise ValueError("请设置RAPIDAPI_KEY环境变量")
    
    server = BookingMCPServer(api_key)
    server.run()
```

## 🌤️ 3. 天气和汇率MCP工具

```python
# tools/mcp_servers/weather_currency_server.py
from mcp.server import FastMCP
import aiohttp
import json
from typing import Dict, Any

class WeatherCurrencyServer:
    def __init__(self, weather_api_key: str, currency_api_key: str = ""):
        self.weather_api_key = weather_api_key
        self.currency_api_key = currency_api_key
        self.mcp = FastMCP("WeatherCurrency", port=8006)
        self._setup_tools()
    
    def _setup_tools(self):
        """设置天气和汇率工具"""
        
        @self.mcp.tool()
        async def get_weather_forecast(
            city: str,
            days: int = 7
        ) -> Dict[str, Any]:
            """
            获取天气预报
            
            Args:
                city: 城市名称
                days: 预报天数
                
            Returns:
                天气预报信息
            """
            return await self._get_weather_forecast(city, days)
        
        @self.mcp.tool()
        async def get_current_weather(city: str) -> Dict[str, Any]:
            """
            获取当前天气
            
            Args:
                city: 城市名称
                
            Returns:
                当前天气信息
            """
            return await self._get_current_weather(city)
        
        @self.mcp.tool()
        async def convert_currency(
            amount: float,
            from_currency: str,
            to_currency: str
        ) -> Dict[str, Any]:
            """
            货币转换
            
            Args:
                amount: 金额
                from_currency: 源货币代码，如USD
                to_currency: 目标货币代码，如CNY
                
            Returns:
                转换结果
            """
            return await self._convert_currency(amount, from_currency, to_currency)
        
        @self.mcp.tool()
        async def get_exchange_rates(base_currency: str = "CNY") -> Dict[str, Any]:
            """
            获取汇率信息
            
            Args:
                base_currency: 基础货币
                
            Returns:
                汇率信息
            """
            return await self._get_exchange_rates(base_currency)
    
    async def _get_weather_forecast(self, city: str, days: int) -> Dict:
        """获取天气预报"""
        url = f"http://api.weatherapi.com/v1/forecast.json"
        params = {
            "key": self.weather_api_key,
            "q": city,
            "days": min(days, 10),  # 最多10天
            "aqi": "yes",
            "alerts": "yes"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_weather_forecast(data)
                    else:
                        return {"error": f"天气API请求失败: {response.status}"}
            except Exception as e:
                return {"error": f"网络请求错误: {str(e)}"}
    
    async def _get_current_weather(self, city: str) -> Dict:
        """获取当前天气"""
        url = f"http://api.weatherapi.com/v1/current.json"
        params = {
            "key": self.weather_api_key,
            "q": city,
            "aqi": "yes"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_current_weather(data)
                    else:
                        return {"error": f"天气API请求失败: {response.status}"}
            except Exception as e:
                return {"error": f"网络请求错误: {str(e)}"}
    
    def _format_weather_forecast(self, raw_data: Dict) -> Dict:
        """格式化天气预报数据"""
        location = raw_data.get("location", {})
        forecast = raw_data.get("forecast", {}).get("forecastday", [])
        
        formatted_forecast = []
        for day in forecast:
            day_data = day.get("day", {})
            formatted_day = {
                "date": day.get("date"),
                "max_temp": day_data.get("maxtemp_c"),
                "min_temp": day_data.get("mintemp_c"),
                "condition": day_data.get("condition", {}).get("text"),
                "condition_icon": day_data.get("condition", {}).get("icon"),
                "humidity": day_data.get("avghumidity"),
                "rain_chance": day_data.get("daily_chance_of_rain"),
                "wind_speed": day_data.get("maxwind_kph"),
                "sunrise": day.get("astro", {}).get("sunrise"),
                "sunset": day.get("astro", {}).get("sunset")
            }
            formatted_forecast.append(formatted_day)
        
        return {
            "status": "success",
            "location": {
                "name": location.get("name"),
                "country": location.get("country"),
                "timezone": location.get("tz_id")
            },
            "forecast": formatted_forecast
        }
    
    def _format_current_weather(self, raw_data: Dict) -> Dict:
        """格式化当前天气数据"""
        location = raw_data.get("location", {})
        current = raw_data.get("current", {})
        
        return {
            "status": "success",
            "location": {
                "name": location.get("name"),
                "country": location.get("country"),
                "local_time": location.get("localtime")
            },
            "current": {
                "temperature": current.get("temp_c"),
                "condition": current.get("condition", {}).get("text"),
                "condition_icon": current.get("condition", {}).get("icon"),
                "humidity": current.get("humidity"),
                "wind_speed": current.get("wind_kph"),
                "visibility": current.get("vis_km"),
                "uv_index": current.get("uv"),
                "feels_like": current.get("feelslike_c")
            }
        }
    
    async def _convert_currency(self, amount: float, from_curr: str, to_curr: str) -> Dict:
        """货币转换"""
        # 使用免费的汇率API
        url = f"https://api.exchangerate-api.com/v4/latest/{from_curr}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data.get("rates", {})
                        
                        if to_curr in rates:
                            rate = rates[to_curr]
                            converted_amount = amount * rate
                            
                            return {
                                "status": "success",
                                "from": {"amount": amount, "currency": from_curr},
                                "to": {"amount": round(converted_amount, 2), "currency": to_curr},
                                "rate": rate,
                                "date": data.get("date")
                            }
                        else:
                            return {"error": f"不支持的货币: {to_curr}"}
                    else:
                        return {"error": f"汇率API请求失败: {response.status}"}
            except Exception as e:
                return {"error": f"网络请求错误: {str(e)}"}
    
    async def _get_exchange_rates(self, base_currency: str) -> Dict:
        """获取汇率"""
        url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 筛选主要货币
                        main_currencies = ["USD", "EUR", "GBP", "JPY", "CNY", "KRW", "THB", "SGD"]
                        main_rates = {curr: data["rates"].get(curr, 0) 
                                    for curr in main_currencies 
                                    if curr in data["rates"]}
                        
                        return {
                            "status": "success",
                            "base": base_currency,
                            "date": data.get("date"),
                            "rates": main_rates
                        }
                    else:
                        return {"error": f"汇率API请求失败: {response.status}"}
            except Exception as e:
                return {"error": f"网络请求错误: {str(e)}"}
    
    def run(self):
        """启动MCP服务器"""
        self.mcp.run(transport="streamable-http")

if __name__ == "__main__":
    import os
    weather_key = os.getenv("WEATHER_API_KEY")
    currency_key = os.getenv("CURRENCY_API_KEY", "")
    
    if not weather_key:
        raise ValueError("请设置WEATHER_API_KEY环境变量")
    
    server = WeatherCurrencyServer(weather_key, currency_key)
    server.run()
```

## 🔧 4. MCP客户端集成器

```python
# tools/mcp_client_manager.py
import asyncio
from typing import Dict, List, Any
from agentscope.mcp import StdIOStatefulClient

class MCPClientManager:
    """MCP客户端管理器"""
    
    def __init__(self, settings):
        self.settings = settings
        self.clients = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """初始化所有MCP客户端"""
        
        # Tavily搜索客户端
        self.clients["tavily"] = StdIOStatefulClient(
            name="tavily_search",
            command="npx",
            args=["-y", "tavily-mcp@latest"],
            env={"TAVILY_API_KEY": self.settings.tavily_api_key}
        )
        
        # 高德POI客户端
        self.clients["amap_poi"] = StdIOStatefulClient(
            name="amap_poi",
            command="python",
            args=["-m", "tools.mcp_servers.amap_poi_server"],
            env={"AMAP_API_KEY": self.settings.amap_api_key}
        )
        
        # 高德路线客户端
        self.clients["amap_route"] = StdIOStatefulClient(
            name="amap_route", 
            command="python",
            args=["-m", "tools.mcp_servers.amap_route_server"],
            env={"AMAP_API_KEY": self.settings.amap_api_key}
        )
        
        # Booking住宿客户端
        self.clients["booking"] = StdIOStatefulClient(
            name="booking",
            command="python", 
            args=["-m", "tools.mcp_servers.booking_mcp_server"],
            env={"RAPIDAPI_KEY": self.settings.rapidapi_key}
        )
        
        # 天气货币客户端
        self.clients["weather_currency"] = StdIOStatefulClient(
            name="weather_currency",
            command="python",
            args=["-m", "tools.mcp_servers.weather_currency_server"],
            env={
                "WEATHER_API_KEY": self.settings.weather_api_key,
                "CURRENCY_API_KEY": getattr(self.settings, 'currency_api_key', '')
            }
        )
    
    async def connect_all(self):
        """连接所有MCP客户端"""
        for name, client in self.clients.items():
            try:
                await client.connect()
                print(f"✅ 已连接MCP客户端: {name}")
            except Exception as e:
                print(f"❌ 连接MCP客户端失败 {name}: {e}")
    
    async def disconnect_all(self):
        """断开所有MCP客户端"""
        for name, client in self.clients.items():
            try:
                await client.close()
                print(f"✅ 已断开MCP客户端: {name}")
            except Exception as e:
                print(f"❌ 断开MCP客户端失败 {name}: {e}")
    
    def get_client(self, name: str):
        """获取指定的MCP客户端"""
        return self.clients.get(name)
    
    async def search_pois(self, city: str, keywords: str) -> Dict[str, Any]:
        """搜索POI"""
        client = self.get_client("amap_poi")
        if not client:
            return {"error": "高德POI客户端未连接"}
        
        try:
            result = await client.call_tool("search_pois", {
                "city": city,
                "keywords": keywords,
                "page_size": 20
            })
            return result
        except Exception as e:
            return {"error": f"POI搜索失败: {str(e)}"}
    
    async def plan_route(self, origin: str, destination: str, waypoints: List[str] = None) -> Dict[str, Any]:
        """规划路线"""
        client = self.get_client("amap_route")
        if not client:
            return {"error": "高德路线客户端未连接"}
        
        try:
            waypoints_str = ";".join(waypoints) if waypoints else ""
            result = await client.call_tool("plan_driving_route", {
                "origin": origin,
                "destination": destination,
                "waypoints": waypoints_str
            })
            return result
        except Exception as e:
            return {"error": f"路线规划失败: {str(e)}"}
    
    async def search_hotels(self, city: str, checkin: str, checkout: str, adults: int = 2) -> Dict[str, Any]:
        """搜索酒店"""
        client = self.get_client("booking")
        if not client:
            return {"error": "Booking客户端未连接"}
        
        try:
            result = await client.call_tool("search_hotels", {
                "city": city,
                "checkin_date": checkin,
                "checkout_date": checkout,
                "adults": adults
            })
            return result
        except Exception as e:
            return {"error": f"酒店搜索失败: {str(e)}"}
    
    async def get_weather(self, city: str, days: int = 7) -> Dict[str, Any]:
        """获取天气"""
        client = self.get_client("weather_currency")
        if not client:
            return {"error": "天气客户端未连接"}
        
        try:
            result = await client.call_tool("get_weather_forecast", {
                "city": city,
                "days": days
            })
            return result
        except Exception as e:
            return {"error": f"天气查询失败: {str(e)}"}
    
    async def search_general(self, query: str) -> Dict[str, Any]:
        """通用搜索"""
        client = self.get_client("tavily")
        if not client:
            return {"error": "Tavily搜索客户端未连接"}
        
        try:
            result = await client.call_tool("search", {
                "query": query,
                "max_results": 10
            })
            return result
        except Exception as e:
            return {"error": f"搜索失败: {str(e)}"}
```

## 📝 5. 更新配置文件

```python
# config.py
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # LLM API配置
    api_key: str = "sk-your-api-key"
    base_url: str = "https://api.moonshot.cn/v1"
    
    # 搜索配置
    tavily_api_key: str = "your-tavily-key"
    
    # 高德地图配置
    amap_api_key: str = "your-amap-key"
    
    # Booking.com配置 (通过RapidAPI)
    rapidapi_key: str = "your-rapidapi-key"
    
    # 天气API配置
    weather_api_key: str = "your-weather-key"
    
    # 汇率API配置 (可选)
    currency_api_key: str = ""
    
    # 应用配置
    debug: bool = True
    
    class Config:
        env_file = ".env"

def get_settings():
    return Settings()
```

## 🚀 6. 启动脚本

```bash
# start_mcp_servers.sh
#!/bin/bash

echo "启动所有MCP服务器..."

# 启动高德POI服务器
python -m tools.mcp_servers.amap_poi_server &
echo "✅ 高德POI服务器启动 (端口8003)"

# 启动高德路线服务器  
python -m tools.mcp_servers.amap_route_server &
echo "✅ 高德路线服务器启动 (端口8004)"

# 启动Booking服务器
python -m tools.mcp_servers.booking_mcp_server &
echo "✅ Booking服务器启动 (端口8005)"

# 启动天气货币服务器
python -m tools.mcp_servers.weather_currency_server &
echo "✅ 天气货币服务器启动 (端口8006)"

echo "所有MCP服务器已启动完成！"
echo "请确保已设置相应的API密钥环境变量"
```

## 🎯 7. 环境变量配置示例

```bash
# .env
# LLM配置
API_KEY=sk-your-moonshot-api-key
BASE_URL=https://api.moonshot.cn/v1

# 搜索配置
TAVILY_API_KEY=tvly-your-tavily-key

# 高德地图配置
AMAP_API_KEY=your-amap-api-key

# RapidAPI配置 (用于Booking.com)
RAPIDAPI_KEY=your-rapidapi-key

# 天气API配置
WEATHER_API_KEY=your-weatherapi-key

# 其他可选配置
CURRENCY_API_KEY=your-currency-api-key
DEBUG=true
```

这样你就有了一个完整的基于真实数据源的MCP工具生态系统，可以获取：

- ✅ **真实POI数据** (高德地图)
- ✅ **精确路线规划** (高德路线)
- ✅ **实时住宿信息** (Booking.com)
- ✅ **天气预报** (WeatherAPI)
- ✅ **汇率转换** (ExchangeRate-API)
- ✅ **通用搜索** (Tavily)

所有数据都来自真实的API，确保信息的准确性和时效性！

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "\u8bbe\u8ba1\u771f\u5b9e\u6570\u636e\u6e90\u7684MCP\u5de5\u5177\u96c6\u6210\u65b9\u6848", "status": "completed", "activeForm": "\u8bbe\u8ba1\u771f\u5b9e\u6570\u636e\u6e90\u7684MCP\u5de5\u5177\u96c6\u6210\u65b9\u6848"}, {"content": "\u5b9e\u73b0\u9ad8\u5fb7\u5730\u56fePOI\u641c\u7d22MCP\u5de5\u5177", "status": "completed", "activeForm": "\u5b9e\u73b0\u9ad8\u5fb7\u5730\u56fePOI\u641c\u7d22MCP\u5de5\u5177"}, {"content": "\u96c6\u6210\u591a\u4e2a\u771f\u5b9e\u6570\u636e\u6e90MCP\u5ba2\u6237\u7aef", "status": "completed", "activeForm": "\u96c6\u6210\u591a\u4e2a\u771f\u5b9e\u6570\u636e\u6e90MCP\u5ba2\u6237\u7aef"}, {"content": "\u66f4\u65b0Agent\u5b9e\u73b0\u4ee5\u4f7f\u7528\u771f\u5b9e\u6570\u636e", "status": "pending", "activeForm": "\u66f4\u65b0Agent\u5b9e\u73b0\u4ee5\u4f7f\u7528\u771f\u5b9e\u6570\u636e"}]