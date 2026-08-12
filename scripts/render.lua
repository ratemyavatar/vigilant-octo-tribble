-- RCC thumbnail render. Tokens {{BASE_URL}} {{ASSET_ID}} {{USER_ID}} {{KIND}} {{KEY}}
-- After a PNG is produced, POST it to {{BASE_URL}}/thumbs/{{KIND}}.ashx?id={{KEY}}
local baseUrl = "{{BASE_URL}}"
local assetId = {{ASSET_ID}}
local userId = {{USER_ID}}
local kind = "{{KIND}}"
local key = "{{KEY}}"

pcall(function()
    game:GetService("ContentProvider"):SetBaseUrl(baseUrl)
    if assetId > 0 then
        print("render-asset " .. tostring(assetId) .. " -> " .. baseUrl .. "/thumbs/" .. kind .. ".ashx?id=" .. key)
    elseif userId > 0 then
        print("render-user " .. tostring(userId) .. " -> " .. baseUrl .. "/thumbs/headshot.ashx?userId=" .. tostring(userId))
    end
end)
