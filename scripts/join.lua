-- Client join script returned by /game/join.ashx
settings().Diagnostics:LegacyScriptMode()
pcall(function() game:SetPlaceId({{PLACE_ID}}) end)
pcall(function() game:SetCreatorId({{CREATOR_ID}}) end)
pcall(function() settings().Network.UseInstancePacketCache = true end)

local nc = game:GetService("NetworkClient")
local suc, err = pcall(function()
    nc:PlayerConnect({{USER_ID}}, "{{HOST}}", {{PORT}})
end)
if not suc then
    print("PlayerConnect failed: " .. tostring(err))
end
