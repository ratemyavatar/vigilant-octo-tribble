-- RCC thumbnail render (2016 RCCService).
-- Tokens filled by server.py: {{BASE_URL}} {{ASSET_ID}} {{USER_ID}} {{KIND}} {{KEY}} {{AVATAR_JSON}}
-- Renders a headshot (userId > 0) or a catalog asset (assetId > 0), then
-- POSTs the PNG back to the site's /thumbs/... endpoint as JSON, the same
-- way the 2016 RCC scripts used by Economy Simulator do it.
local baseUrl = "{{BASE_URL}}"
local assetId = {{ASSET_ID}}
local userId = {{USER_ID}}
local kind = "{{KIND}}"
local key = "{{KEY}}"

local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local InsertService = game:GetService("InsertService")
local ThumbnailGenerator = game:GetService("ThumbnailGenerator")

pcall(function() game:GetService("StarterGui"):SetCoreGuiEnabled(Enum.CoreGuiType.All, false) end)
pcall(function() game:GetService("ScriptContext").ScriptsDisabled = true end)
pcall(function() game:GetService("Lighting").Outlines = false end)
pcall(function() game:GetService("ContentProvider"):SetBaseUrl(baseUrl .. "/") end)
pcall(function() InsertService:SetAssetUrl(baseUrl .. "/asset/?id=%d") end)
pcall(function() InsertService:SetAssetVersionUrl(baseUrl .. "/asset/?assetversionid=%d") end)
ThumbnailGenerator.GraphicsMode = 2
HttpService.HttpEnabled = true

local uploadUrl = "{{UPLOAD_URL}}"

local function postThumbnail(encoded)
    if type(encoded) ~= "string" or #encoded == 0 then
        print("[render] empty thumbnail, skipping post")
        return
    end
    local ok, err = pcall(function()
        HttpService:PostAsync(uploadUrl, HttpService:JSONEncode({
            thumbnail = encoded,
            id = key,
            userId = userId,
            kind = kind,
        }), Enum.HttpContentType.ApplicationJson)
    end)
    if not ok then
        print("[render] post failed: " .. tostring(err))
    else
        print("[render] posted " .. kind .. " " .. tostring(key) .. " -> " .. uploadUrl)
    end
end

local function hexToColor3(hex)
    local h = tostring(hex or ""):gsub("#", "")
    if #h ~= 6 then
        return nil
    end
    local r = tonumber(h:sub(1, 2), 16)
    local g = tonumber(h:sub(3, 4), 16)
    local b = tonumber(h:sub(5, 6), 16)
    if not r or not g or not b then
        return nil
    end
    return Color3.new(r / 255, g / 255, b / 255)
end

local function renderHeadshot()
    local player = Players:CreateLocalPlayer(userId)
    player:LoadCharacter()

    -- Avatar data comes from the site in the same shape Economy Simulator
    -- sends (assets + bodyColors), filled into {{AVATAR_JSON}}.
    local av = {{AVATAR_JSON}}

    -- Body colors
    local char = player.Character
    local bc = av.bodyColors or {}
    for part, hex in pairs(bc) do
        local limb = char:FindFirstChild(part)
        local c3 = hexToColor3(hex)
        if limb and c3 then
            pcall(function() limb.BrickColor = BrickColor.new(c3) end)
        end
    end

    -- Worn assets
    local assets = av.assets or {}
    local done = 0
    for _, asset in pairs(assets) do
        coroutine.wrap(function()
            local ok, model = pcall(function()
                return InsertService:LoadAsset(asset.id)
            end)
            if ok then
                local children = model:GetChildren()
                for _, item in pairs(children) do
                    item.Parent = char
                    if asset.assetType == 18 then
                        -- Face: parent under the Head, replace old face
                        local head = char:FindFirstChild("Head")
                        if head then
                            local old = head:FindFirstChild("face")
                            if old then
                                old:Destroy()
                            end
                            item.Name = "face"
                            item.Parent = head
                        end
                    elseif asset.assetType == 17 and char:FindFirstChild("Head") then
                        -- Mesh for the head
                        item.Parent = char.Head
                    end
                end
            else
                print("[render] load asset failed: " .. tostring(asset.id))
            end
            done = done + 1
        end)()
    end
    repeat wait() until done == #assets

    -- Drop tools/gear so the bust stays clean
    for _, child in pairs(char:GetChildren()) do
        if child:IsA("Tool") then
            child:Destroy()
        end
    end

    -- Camera in front of the head
    local head = char:FindFirstChild("Head")
    if not head then
        return
    end
    local viewOffset = head.CFrame * CFrame.new(0, 0.5, 0.1)
    local positionOffset = head.CFrame + (CFrame.Angles(0, -math.pi / 16, 0).lookVector.unit * 3)
    local camera = game.Workspace.CurrentCamera
    camera.CameraType = Enum.CameraType.Scriptable
    camera.CoordinateFrame = CFrame.new(positionOffset.p, viewOffset.p)
    camera.FieldOfView = 40

    local encoded = ThumbnailGenerator:Click("png", 420, 420, true, true)
    postThumbnail(encoded)
end

local function renderAsset()
    local ok, model = pcall(function()
        return InsertService:LoadAsset(assetId)
    end)
    if not ok then
        print("[render] asset load failed: " .. tostring(assetId))
        return
    end
    model.Parent = game.Workspace

    local camera = game.Workspace.CurrentCamera
    camera.CameraType = Enum.CameraType.Scriptable
    local cframe, size = nil, nil
    pcall(function()
        cframe, size = model:GetBoundingBox()
    end)
    if not cframe then
        cframe = model:GetModelCFrame()
        size = Vector3.new(4, 4, 4)
    end
    local dist = math.max(size.x, size.y, size.z) * 1.6 + 2
    camera.CoordinateFrame = cframe * CFrame.new(0, 0, dist)
    camera.FieldOfView = 40

    local encoded = ThumbnailGenerator:Click("png", 420, 420, false, true)
    postThumbnail(encoded)
end

local ok, err = pcall(function()
    if userId > 0 then
        renderHeadshot()
    elseif assetId > 0 then
        renderAsset()
    else
        print("[render] nothing to render")
    end
end)
if not ok then
    print("[render] failed: " .. tostring(err))
end
