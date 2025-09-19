## 高德
```json
{
  "name": "高德-个人",
  "type": "streamableHttp",
  "description": "",
  "isActive": true,
  "baseUrl": "https://mcp.amap.com/mcp?key=9105a7f9617c226c0e5f49d059944354"
}
```

## 天气
```json
{
  "name": "jdo-天气",
  "type": "streamableHttp",
  "description": "",
  "isActive": true,
  "baseUrl": "https://aigc-mcp-api-test.aijidou.com/mcp/weather/streamable",
  "headers": {
    "apikey": "690fd8653d0ee9c2f552459349e5faef"
  }
}
```

## 小红书
- https://github.com/jobsonlook/xhs-mcp
- 路径配置：在 config.py 中的 xhs_mcp_directory 设置
```json
{
  "command": "uv",
  "args": [
    "--directory",
    "{从config.py读取xhs_mcp_directory}",
    "run",
    "main.py"
  ],
  "env": {
    "XHS_COOKIE": "a1=1940627219618wm14yddam6g0hbnswnmmclc7daj430000142908; webId=ee0b066b0d22c21d1822fe73be3d20a6; gid=yj48KJWJKi6Dyj48KJWJySf0jKyYE6y4vff01V46Kk8xDSq8IMEI6W888y4Jj8Y8yiDqqjWi; abRequestId=ee0b066b0d22c21d1822fe73be3d20a6; web_session=0400698e5867e656d08d9dbbbc354bfd4a9550; x-user-id-creator.xiaohongshu.com=5f2c24ae00000000010080db; customerClientId=253070019720926; webBuild=4.81.0; xsecappid=xhs-pc-web; acw_tc=0a00df6217582831520252648e5aef76f4a9fb252e693872f8b54d30ccfcb8; websectiga=3fff3a6f9f07284b62c0f2ebf91a3b10193175c06e4f71492b60e056edcdebb2; sec_poison_id=756416ec-2730-486e-a55e-589e215d65db; loadts=1758283157647; unread={%22ub%22:%2268c508bb000000001c034681%22%2C%22ue%22:%2268c546bf000000001d0097d4%22%2C%22uc%22:25}"
  },
  "name": "xhs-mcp",
  "baseUrl": "",
  "isActive": true,
  "disabledTools": [
    "post_comment",
    "home_feed",
    "get_note_comments"
  ]
}
```

## 搜索 ()
```python
    mcp_clients.append(
        StdIOStatefulClient(
            name="tavily_mcp",
            command="npx",
            args=["-y", "tavily-mcp@latest"],
            env={"TAVILY_API_KEY": tavily_key},
        ),
    )
```