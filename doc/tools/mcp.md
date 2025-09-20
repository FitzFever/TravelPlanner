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
    "XHS_COOKIE": "abRequestId=6e12629e-86a3-59d3-9177-a908d77fdf1a; xsecappid=xhs-pc-web; a1=19744a844a5r6ncvxrpc6bzhhpeuam8a6068zw4eo30000782193; webId=af7afdd61d64eb3bce723fee54929418; gid=yjW08iidfiKWyjW440Y448E402FKIShCFUSKKdlDuxxUdYq8706Y0u888WYJyjq8KjySj8W8; webBuild=4.81.0; web_session=04006979827162156355bc2ff83a4bac04becb; acw_tc=0a4ae10f17583562845381940ef2d1982f904b71c4581f8e0cbb76ad6d5ee4; websectiga=10f9a40ba454a07755a08f27ef8194c53637eba4551cf9751c009d9afb564467; sec_poison_id=0bdc24b7-8009-4626-b792-ebda2cdd6281; unread={%22ub%22:%2268cd005c0000000013004b35%22%2C%22ue%22:%2268bedc45000000001b033c8c%22%2C%22uc%22:26}; loadts=1758357627361"
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