local SandboxEngine = {
    version = "3.1.0",
    execution_limit = 8
}

function SandboxEngine:initialize()
    self.trace_log = {}
    self.execution_stack = {}
    self.virtual_objects = {}
    self.intercepted_calls = 0
    self.start_time = os.clock()
end

function SandboxEngine:record(event, details)
    local entry = {
        time = os.clock() - self.start_time,
        event = event,
        details = details
    }
    table.insert(self.trace_log, entry)
    return entry
end

function SandboxEngine:make_secure_object(object_name, properties)
    local obj = properties or {}
    local meta = {}
    
    meta.__index = function(t, key)
        self:record("property_access", {object = object_name, property = key})
        if obj[key] then
            return obj[key]
        end
        return self:make_secure_object(key, {})
    end
    
    meta.__newindex = function(t, key, value)
        self:record("property_set", {object = object_name, property = key, value_type = type(value)})
        rawset(obj, key, value)
    end
    
    meta.__tostring = function()
        return "<SecureObject:" .. object_name .. ">"
    end
    
    return setmetatable({}, meta)
end

function SandboxEngine:build_vector_math()
    local VectorMath = {}
    
    function VectorMath.create(x, y, z)
        return {
            x = x or 0,
            y = y or 0,
            z = z or 0,
            magnitude = math.sqrt((x or 0)^2 + (y or 0)^2 + (z or 0)^2)
        }
    end
    
    function VectorMath.add(a, b)
        return VectorMath.create(a.x + b.x, a.y + b.y, a.z + b.z)
    end
    
    function VectorMath.dot(a, b)
        return a.x * b.x + a.y * b.y + a.z * b.z
    end
    
    return VectorMath
end

function SandboxEngine:create_roblox_api()
    local API = {}
    
    API.Game = self:make_secure_object("Game", {
        Workspace = self:make_secure_object("Workspace"),
        Players = self:make_secure_object("Players"),
        Lighting = self:make_secure_object("Lighting")
    })
    
    API.Instances = {}
    
    function API.Instances.create(class_name)
        local instance = self:make_secure_object(class_name, {
            Name = class_name,
            Parent = nil,
            Destroy = function()
                self:record("instance_destroy", {class = class_name})
            end
        })
        
        local class_methods = {
            Part = {Size = Vector3.new(1, 1, 1), BrickColor = BrickColor.new("Bright green")},
            Script = {Source = "", Disabled = false},
            Humanoid = {Health = 100, WalkSpeed = 16}
        }
        
        if class_methods[class_name] then
            for k, v in pairs(class_methods[class_name]) do
                instance[k] = v
            end
        end
        
        return instance
    end
    
    return API
end

function SandboxEngine:execute_lua(code, timeout)
    timeout = timeout or self.execution_limit
    local success, result = pcall(function()
        local env = {}
        
        setmetatable(env, {
            __index = function(t, k)
                if k == "game" then
                    return self:create_roblox_api().Game
                elseif k == "Vector3" then
                    return self:build_vector_math()
                elseif k == "print" then
                    return function(...)
                        self:record("print_output", {...})
                    end
                end
                return nil
            end
        })
        
        local func, err = loadstring(code)
        if not func then
            error("Compilation failed: " .. tostring(err))
        end
        
        setfenv(func, env)
        
        local hook = function()
            if os.clock() - self.start_time > timeout then
                error("Execution timeout exceeded")
            end
        end
        
        debug.sethook(hook, "", 10000)
        
        local results = {func()}
        debug.sethook()
        
        return results
    end)
    
    return success, result, self.trace_log
end

return SandboxEngine
