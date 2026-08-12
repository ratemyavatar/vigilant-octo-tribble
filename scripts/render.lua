-- RCC thumbnail render. Tokens {{BASE_URL}} {{ASSET_ID}} {{USER_ID}}
local baseUrl = "{{BASE_URL}}"
local assetId = {{ASSET_ID}}
local userId = {{USER_ID}}

pcall(function()
    if assetId > 0 then
        game:GetService("ContentProvider"):SetBaseUrl(baseUrl)
        print("render-asset " .. tostring(assetId))
    elseif userId > 0 then
        print("render-user " .. tostring(userId))
    end
end)
