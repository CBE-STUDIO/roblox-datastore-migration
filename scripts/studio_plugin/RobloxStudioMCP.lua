--!strict
--[[
    RobloxStudioMCP.lua  --  Roblox Studio <-> localhost bridge plugin

    Install : drop this file into  %LOCALAPPDATA%\Roblox\Plugins\  then restart Studio
    Bridge  : http://127.0.0.1:8791   (started by scripts/studio_plugin/server.py)
    Needs   : Game Settings > Security > "Allow HTTP Requests" ON

    It runs Lua previously queued by the bridge via a ModuleScript require(),
    so "Enable Load String" is NOT required.

    Bridge protocol
      GET  /poll           -> {id, op, args} | {}
      POST /reply {id, ok, data|error}
      POST /hello {plugin, place, placeId, ...}
      GET  /drop?id=N      -> cancel a queued command (timeouts)
]]

local HttpService = game:GetService("HttpService")
local RunService  = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

if not plugin then
	return
end

local BASE     = "http://127.0.0.1:8791"
local VERSION  = "1.0.0"
local POLL_SEC = 0.25
local alive    = true
local busy     = false
local runSeq   = 0

local function enc(v: any): string
	return HttpService:JSONEncode(v)
end

local function dec(s: string): (any?, string?)
	local ok, v = pcall(function()
		return HttpService:JSONDecode(s)
	end)
	if ok then
		return v, nil
	end
	return nil, "json decode: " .. tostring(v)
end

local function request(method: string, path: string, body: any?): (any?, string?)
	local opts: any = { Url = BASE .. path, Method = method }
	if body ~= nil then
		opts.Body = if type(body) == "string" then body else enc(body)
		opts.Headers = { ["Content-Type"] = "application/json" }
	end
	local ok, res = pcall(function()
		return HttpService:RequestAsync(opts)
	end)
	if not ok then
		return nil, tostring(res)
	end
	if res.Success then
		if res.Body == "" then
			return {}, nil
		end
		return dec(res.Body)
	end
	return nil, string.format("HTTP %s: %s", tostring(res.StatusCode), tostring(res.Body))
end

-- run arbitrary code via a ModuleScript require (no loadstring needed)
local function runLua(code: string): any
	runSeq += 1
	local ms = Instance.new("ModuleScript")
	ms.Name = "__bridge_run_" .. tostring(runSeq)
	ms.Source = "return (function()\n" .. code .. "\nend)()"
	ms.Parent = ServerStorage
	local ok, res = xpcall(function()
		return require(ms)
	end, function(e)
		return debug.traceback(tostring(e), 2)
	end)
	ms:Destroy()
	if not ok then
		error(res, 0)
	end
	return res
end

local OPS: any = {}

OPS.lua = function(args: any)
	if type(args.code) ~= "string" or args.code == "" then
		error("code required", 0)
	end
	local value = runLua(args.code)
	local ok, encoded = pcall(function()
		return enc(value)
	end)
	return {
		ok = true,
		type = typeof(value),
		value = if ok then dec(encoded) else tostring(value),
	}
end

OPS.ping = function(_args: any)
	local loadstringOk = type(loadstring) == "function"
	return {
		ok = true,
		plugin = VERSION,
		place = game.Name,
		placeId = game.PlaceId,
		universeId = game.UniverseId,
		isStudio = RunService:IsStudio(),
		loadstring = loadstringOk,
	}
end

local toolbar = plugin:CreateToolbar("MCP Bridge")
local btn = toolbar:CreateButton("MCP", "Toggle bridge (" .. BASE .. ")", "rbxassetid://6031075931")

local function status()
	pcall(function()
		btn:SetActive(alive)
	end)
end
status()

local function hello()
	request("POST", "/hello", {
		plugin = VERSION, place = game.Name, placeId = game.PlaceId,
	})
end

local function handshakeLoop()
	while alive do
		if not busy then
			local res, err = request("GET", "/poll")
			if res and res.cmd then
				busy = true
				local cmd = res.cmd
				local ok, data
				local opFn = OPS[cmd.op]
				if opFn then
					ok, data = pcall(opFn, cmd.args or {})
					if ok then
						request("POST", "/reply", { id = cmd.id, ok = true, data = data })
					else
						request("POST", "/reply", { id = cmd.id, ok = false, error = tostring(data) })
					end
				else
					request("POST", "/reply", { id = cmd.id, ok = false, error = "unknown op: " .. tostring(cmd.op) })
				end
				busy = false
			end
		end
		task.wait(POLL_SEC)
	end
end

btn.Click:Connect(function()
	alive = not alive
	status()
	if alive then
		task.spawn(handshakeLoop)
	end
end)

task.spawn(function()
	task.wait(1)
	hello()
	handshakeLoop()
end)

print("[MCP] RobloxStudioMCP v" .. VERSION .. " loaded -> " .. BASE)
