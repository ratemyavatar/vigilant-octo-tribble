-- RCC game job. Tokens {{PLACE_ID}} {{PORT}} {{BASE_URL}} {{MAX_PLAYERS}} are filled by the site.
pcall(function() settings().Network.UseInstancePacketCache = true end)
pcall(function() settings().Network.UsePhysicsPacketCache = true end)
pcall(function() settings().Network.PhysicsSend = 12 end)
pcall(function() settings().Rendering.QualityLevel = 1 end)

local placeId = {{PLACE_ID}}
local port = {{PORT}}
local baseUrl = "{{BASE_URL}}"
local maxPlayers = {{MAX_PLAYERS}}

pcall(function()
    game:GetService("Players").MaxPlayers = maxPlayers
end)

local ok, err = pcall(function()
    game:Load(baseUrl .. "/asset/?id=" .. tostring(placeId))
end)
if not ok then
    print("Load failed: " .. tostring(err))
end

local ns = game:GetService("NetworkServer")
ns:Start(port)
game:GetService("RunService"):Run()
print("Game server started place=" .. tostring(placeId) .. " port=" .. tostring(port))
