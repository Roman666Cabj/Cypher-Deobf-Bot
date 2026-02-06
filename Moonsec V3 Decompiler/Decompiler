local bytecode_source = arg[1] or "ByteCode.luac"
local output_destination = arg[2] or "DecompiledOutput.lua"

local function arithmetic_shift_right(value, shift_amount)
    return math.floor(value / 2 ^ shift_amount)
end

local function binary_and(operand_a, operand_b)
    local position_value, result = 1, 0
    while operand_a > 0 and operand_b > 0 do
        local remainder_a = operand_a % 2
        local remainder_b = operand_b % 2
        if remainder_a + remainder_b > 1 then
            result = result + position_value
        end
        operand_a = (operand_a - remainder_a) / 2
        operand_b = (operand_b - remainder_b) / 2
        position_value = position_value * 2
    end
    return result
end

local InstructionSet = {
    MOVE = 0,
    LOADK = 1,
    LOADBOOL = 2,
    LOADNIL = 3,
    GETUPVAL = 4,
    GETGLOBAL = 5,
    GETTABLE = 6,
    SETGLOBAL = 7,
    SETUPVAL = 8,
    SETTABLE = 9,
    NEWTABLE = 10,
    SELF = 11,
    ADD = 12,
    SUB = 13,
    MUL = 14,
    DIV = 15,
    MOD = 16,
    POW = 17,
    UNM = 18,
    NOT = 19,
    LEN = 20,
    CONCAT = 21,
    JMP = 22,
    EQ = 23,
    LT = 24,
    LE = 25,
    TEST = 26,
    TESTSET = 27,
    CALL = 28,
    TAILCALL = 29,
    RETURN = 30,
    FORLOOP = 31,
    FORPREP = 32,
    TFORLOOP = 33,
    SETLIST = 34,
    CLOSE = 35,
    CLOSURE = 36,
    VARARG = 37
}

local InstructionNames = {}
for key, value in pairs(InstructionSet) do
    InstructionNames[value] = key
end

local BytecodeProcessor = {
    content = "",
    position = 1,
    little_endian = true,
    integer_size = 4,
    size_type = 4
}

BytecodeProcessor.__index = BytecodeProcessor

function BytecodeProcessor:initialize(byte_data)
    local processor = setmetatable({
        content = byte_data,
        position = 1
    }, BytecodeProcessor)
    return processor
end

function BytecodeProcessor:read_byte()
    local byte_value = self.content:byte(self.position)
    self.position = self.position + 1
    return byte_value
end

function BytecodeProcessor:read_bytes(quantity)
    local byte_collection = {}
    for i = 1, quantity do
        local byte_value = self:read_byte()
        if not byte_value then return nil end
        table.insert(byte_collection, byte_value)
    end
    return byte_collection
end

function BytecodeProcessor:read_integer(size)
    local byte_data = self:read_bytes(size)
    if not byte_data then return nil end
    
    local accumulated = 0
    if self.little_endian then
        for i = 1, size do
            accumulated = accumulated + byte_data[i] * (2 ^ ((i - 1) * 8))
        end
    else
        for i = 1, size do
            accumulated = accumulated + byte_data[i] * (2 ^ ((size - i) * 8))
        end
    end
    return accumulated
end

function BytecodeProcessor:read_integer_value()
    return self:read_integer(self.integer_size)
end

function BytecodeProcessor:read_size_type()
    return self:read_integer(self.size_type)
end

function BytecodeProcessor:read_numeric()
    local byte_data = self:read_bytes(8)
    if not byte_data then return 0 end
    
    if not self.little_endian then
        local reversed = {}
        for i = 8, 1, -1 do
            reversed[9 - i] = byte_data[i]
        end
        byte_data = reversed
    end
    
    local sign_multiplier = (byte_data[8] > 127) and -1 or 1
    local exponent = binary_and(byte_data[8], 127) * 16 + arithmetic_shift_right(byte_data[7], 4)
    local mantissa = binary_and(byte_data[7], 15)
    
    for i = 6, 1, -1 do
        mantissa = mantissa * 256 + byte_data[i]
    end
    
    if exponent == 0 then
        return (mantissa == 0) and 0 or sign_multiplier * mantissa * 3.4175792574734563e-227
    elseif exponent == 2047 then
        return (mantissa == 0) and sign_multiplier * (1 / 0) or 0 / 0
    end
    
    return sign_multiplier * (1 + mantissa / (2 ^ 52)) * (2 ^ (exponent - 1023))
end

function BytecodeProcessor:read_string()
    local length = self:read_size_type()
    if not length or length == 0 then return nil end
    
    local extracted = self.content:sub(self.position, self.position + length - 2)
    self.position = self.position + length
    return extracted
end

local function process_header(processor)
    assert(processor:read_byte() == 27 and processor:read_byte() == 76 and processor:read_byte() == 117 and processor:read_byte() == 97, "Invalid Lua bytecode format")
    local version_number = processor:read_byte()
    local format_version = processor:read_byte()
    local endian_flag = processor:read_byte()
    processor.little_endian = (endian_flag == 1)
    processor.integer_size = processor:read_byte()
    processor.size_type = processor:read_byte()
    local instruction_size = processor:read_byte()
    local numeric_size = processor:read_byte()
    local integral_flag = processor:read_byte()
end

local function_id_counter = 0

local function process_function(processor, parent_function)
    function_id_counter = function_id_counter + 1
    
    local function_data = {
        identifier = function_id_counter,
        source_name = processor:read_string(),
        start_line = processor:read_integer_value(),
        end_line = processor:read_integer_value(),
        upvalue_count = processor:read_byte(),
        parameter_count = processor:read_byte(),
        variable_arguments = processor:read_byte(),
        stack_limit = processor:read_byte()
    }
    
    local instruction_count = processor:read_integer_value()
    function_data.instructions = {}
    
    for i = 1, instruction_count do
        local instruction_value = processor:read_integer_value()
        local operation_code = instruction_value % 64
        local operand_a = math.floor(instruction_value / 64) % 256
        local operand_c = math.floor(instruction_value / 16384) % 512
        local operand_b = math.floor(instruction_value / 8388608) % 512
        local extended_b = math.floor(instruction_value / 16384) % 262144
        local signed_extended = extended_b - 131071
        
        table.insert(function_data.instructions, {
            opcode = operation_code,
            a = operand_a,
            b = operand_b,
            c = operand_c,
            bx = extended_b,
            sbx = signed_extended
        })
    end
    
    local constant_count = processor:read_integer_value()
    function_data.constants = {}
    
    for i = 1, constant_count do
        local constant_type = processor:read_byte()
        if constant_type == 0 then
            table.insert(function_data.constants, {type = "nil"})
        elseif constant_type == 1 then
            table.insert(function_data.constants, {
                type = "boolean",
                value = processor:read_byte() ~= 0
            })
        elseif constant_type == 3 then
            table.insert(function_data.constants, {
                type = "numeric",
                value = processor:read_numeric()
            })
        elseif constant_type == 4 then
            table.insert(function_data.constants, {
                type = "string",
                value = processor:read_string()
            })
        end
    end
    
    local child_function_count = processor:read_integer_value()
    function_data.children = {}
    
    for i = 1, child_function_count do
        table.insert(function_data.children, process_function(processor, function_data))
    end
    
    local line_info_count = processor:read_integer_value()
    for i = 1, line_info_count do
        processor:read_integer_value()
    end
    
    local local_var_count = processor:read_integer_value()
    for i = 1, local_var_count do
        processor:read_string()
        processor:read_integer_value()
        processor:read_integer_value()
    end
    
    local upvalue_count = processor:read_integer_value()
    for i = 1, upvalue_count do
        processor:read_string()
    end
    
    return function_data
end

local function generate_register_name(register_index, function_id)
    return "reg" .. register_index .. "_" .. (function_id or 0)
end

local function constant_to_string(constant_data)
    if constant_data.type == "nil" then
        return "nil"
    elseif constant_data.type == "boolean" then
        return constant_data.value and "true" or "false"
    elseif constant_data.type == "numeric" then
        return tostring(constant_data.value)
    elseif constant_data.type == "string" then
        return string.format("%q", constant_data.value)
    end
    return "unknown"
end

local function valid_identifier(name)
    return name:match("^[%a_][%w_]*$") ~= nil
end

local function output_line(context, content)
    local indentation = string.rep("  ", context.indentation_level)
    table.insert(context.output_lines, indentation .. content)
end

local function get_register_name(context, register_index)
    if not context.register_names[register_index] then
        context.register_names[register_index] = generate_register_name(register_index, context.function_data.identifier)
    end
    return context.register_names[register_index]
end

local function get_expression(context, register_index)
    return context.expression_map[register_index] or get_register_name(context, register_index)
end

local function set_expression(context, register_index, expression)
    context.expression_map[register_index] = expression
end

local function get_rk_value(context, rk_index)
    if rk_index < 256 then
        return get_expression(context, rk_index)
    else
        return constant_to_string(context.function_data.constants[rk_index - 256 + 1])
    end
end

local function resolve_upvalue(context, index)
    return "upvalue_" .. index
end

local function analyze_control_flow(function_data)
    local instructions = function_data.instructions
    local block_boundaries = {}
    
    for program_counter = 1, #instructions do
        local current_instruction = instructions[program_counter]
        
        if current_instruction.opcode == InstructionSet.EQ or 
           current_instruction.opcode == InstructionSet.LT or 
           current_instruction.opcode == InstructionSet.LE or 
           current_instruction.opcode == InstructionSet.TEST or 
           current_instruction.opcode == InstructionSet.TESTSET then
            
            local next_instruction = instructions[program_counter + 1]
            if next_instruction and next_instruction.opcode == InstructionSet.JMP then
                local jump_target = program_counter + 2 + next_instruction.sbx
                if not block_boundaries[jump_target] then
                    block_boundaries[jump_target] = {}
                end
                table.insert(block_boundaries[jump_target], "conditional")
            else
                if not block_boundaries[program_counter + 2] then
                    block_boundaries[program_counter + 2] = {}
                end
                table.insert(block_boundaries[program_counter + 2], "conditional")
            end
        end
        
        if current_instruction.opcode == InstructionSet.FORPREP then
            local loop_end = program_counter + 1 + current_instruction.sbx + 1
            if not block_boundaries[loop_end] then
                block_boundaries[loop_end] = {}
            end
            table.insert(block_boundaries[loop_end], "iteration")
        end
    end
    
    return {block_boundaries = block_boundaries}
end

local function create_context(function_data, parent_context)
    return {
        function_data = function_data,
        parent_context = parent_context,
        expression_map = {},
        register_names = {},
        declared_registers = {},
        self_information = nil,
        table_data = {},
        pending_closures = {},
        indentation_level = 0,
        output_lines = {},
        flow_analysis = analyze_control_flow(function_data)
    }
end

local function build_table_expression(context, register_index, indentation)
    local table_info = context.table_data[register_index]
    if not table_info then return "{}" end
    
    local table_parts = {}
    for _, entry in ipairs(table_info.entries) do
        if entry.safe_key then
            table.insert(table_parts, entry.key .. " = " .. entry.value)
        else
            table.insert(table_parts, "[" .. entry.key .. "] = " .. entry.value)
        end
    end
    
    for _, value in ipairs(table_info.array_entries) do
        table.insert(table_parts, value)
    end
    
    if #table_parts == 0 then return "{}" end
    
    if #table_parts <= 3 and not table_info.contains_functions then
        return "{" .. table.concat(table_parts, ", ") .. "}"
    end
    
    local formatted_lines = {}
    table.insert(formatted_lines, "{")
    for _, part in ipairs(table_parts) do
        table.insert(formatted_lines, string.rep("  ", indentation + 1) .. part .. ",")
    end
    table.insert(formatted_lines, string.rep("  ", indentation) .. "}")
    return table.concat(formatted_lines, "\n")
end

local function can_inline_function(context, register_index)
    return false
end

local function reconstruct_function

local function reconstruct_inline(context, function_prototype, indentation)
    local child_context = create_context(function_prototype, context)
    child_context.indentation_level = 0
    reconstruct_function(child_context, function_prototype)
    
    local function_lines = {}
    for _, line in ipairs(child_context.output_lines) do
        table.insert(function_lines, line)
    end
    return "function(...)\n" .. table.concat(function_lines, "\n") .. "\nend"
end

function reconstruct_function(context, function_data)
    local instructions = function_data.instructions
    local instruction_count = #instructions
    local program_counter = 1
    local flow_data = context.flow_analysis
    
    while program_counter <= instruction_count do
        if flow_data.block_boundaries[program_counter] then
            for _, block_type in ipairs(flow_data.block_boundaries[program_counter]) do
                context.indentation_level = math.max(0, context.indentation_level - 1)
                output_line(context, "end")
            end
        end
        
        local current_instruction = instructions[program_counter]
        local operation = current_instruction.opcode
        local operand_a = current_instruction.a
        local operand_b = current_instruction.b
        local operand_c = current_instruction.c
        local extended_b = current_instruction.bx
        local signed_extended = current_instruction.sbx
        
        if operation == InstructionSet.MOVE then
            set_expression(context, operand_a, get_expression(context, operand_b))
        
        elseif operation == InstructionSet.LOADK then
            set_expression(context, operand_a, constant_to_string(function_data.constants[extended_b + 1]))
        
        elseif operation == InstructionSet.LOADBOOL then
            set_expression(context, operand_a, operand_b ~= 0 and "true" or "false")
            if operand_c ~= 0 then program_counter = program_counter + 1 end
        
        elseif operation == InstructionSet.LOADNIL then
            for i = operand_a, operand_b do
                set_expression(context, i, "nil")
            end
        
        elseif operation == InstructionSet.GETUPVAL then
            set_expression(context, operand_a, resolve_upvalue(context, operand_b))
        
        elseif operation == InstructionSet.GETGLOBAL then
            set_expression(context, operand_a, function_data.constants[extended_b + 1].value)
        
        elseif operation == InstructionSet.GETTABLE then
            local object_ref = get_expression(context, operand_b)
            local key_value = get_rk_value(context, operand_c)
            
            if operand_c >= 256 then
                local constant_key = function_data.constants[operand_c - 256 + 1]
                if constant_key.type == "string" and valid_identifier(constant_key.value) then
                    set_expression(context, operand_a, object_ref .. "." .. constant_key.value)
                else
                    set_expression(context, operand_a, object_ref .. "[" .. key_value .. "]")
                end
            else
                set_expression(context, operand_a, object_ref .. "[" .. key_value .. "]")
            end
        
        elseif operation == InstructionSet.SETGLOBAL then
            output_line(context, function_data.constants[extended_b + 1].value .. " = " .. get_expression(context, operand_a))
        
        elseif operation == InstructionSet.SETUPVAL then
            output_line(context, resolve_upvalue(context, operand_b) .. " = " .. get_expression(context, operand_a))
        
        elseif operation == InstructionSet.SETTABLE then
            local key_ref = get_rk_value(context, operand_b)
            local value_ref = operand_c < 256 and context.pending_closures[operand_c] or nil
            if not value_ref then value_ref = get_rk_value(context, operand_c) end
            
            if operand_c < 256 then context.pending_closures[operand_c] = nil end
            
            if context.table_data[operand_a] then
                local key_safe = false
                local key_name = key_ref
                if operand_b >= 256 then
                    local constant_key = function_data.constants[operand_b - 256 + 1]
                    if constant_key.type == "string" and valid_identifier(constant_key.value) then
                        key_safe = true
                        key_name = constant_key.value
                    end
                end
                
                if value_ref:match("^function%(") then
                    context.table_data[operand_a].contains_functions = true
                end
                
                table.insert(context.table_data[operand_a].entries, {
                    key = key_name,
                    value = value_ref,
                    safe_key = key_safe
                })
            else
                local object_ref = get_expression(context, operand_a)
                local assignment_target
                if operand_b >= 256 then
                    local constant_key = function_data.constants[operand_b - 256 + 1]
                    if constant_key.type == "string" and valid_identifier(constant_key.value) then
                        assignment_target = object_ref .. "." .. constant_key.value
                    else
                        assignment_target = object_ref .. "[" .. key_ref .. "]"
                    end
                else
                    assignment_target = object_ref .. "[" .. key_ref .. "]"
                end
                output_line(context, assignment_target .. " = " .. value_ref)
            end
        
        elseif operation == InstructionSet.NEWTABLE then
            context.table_data[operand_a] = {
                entries = {},
                array_entries = {},
                contains_functions = false
            }
            set_expression(context, operand_a, nil)
        
        elseif operation == InstructionSet.SELF then
            local object_ref = get_expression(context, operand_b)
            local method_name = nil
            if operand_c >= 256 then
                local constant_method = function_data.constants[operand_c - 256 + 1]
                if constant_method.type == "string" then
                    method_name = constant_method.value
                end
            end
            
            context.self_information = {
                object = object_ref,
                method = method_name,
                method_raw = get_rk_value(context, operand_c)
            }
            
            set_expression(context, operand_a + 1, object_ref)
            if method_name and valid_identifier(method_name) then
                set_expression(context, operand_a, object_ref .. ":" .. method_name)
            else
                set_expression(context, operand_a, object_ref .. "[" .. context.self_information.method_raw .. "]")
            end
        
        elseif operation >= InstructionSet.ADD and operation <= InstructionSet.POW then
            local operator_map = {
                [InstructionSet.ADD] = "+",
                [InstructionSet.SUB] = "-",
                [InstructionSet.MUL] = "*",
                [InstructionSet.DIV] = "/",
                [InstructionSet.MOD] = "%",
                [InstructionSet.POW] = "^"
            }
            set_expression(context, operand_a, get_rk_value(context, operand_b) .. " " .. operator_map[operation] .. " " .. get_rk_value(context, operand_c))
        
        elseif operation == InstructionSet.UNM then
            set_expression(context, operand_a, "-" .. get_expression(context, operand_b))
        
        elseif operation == InstructionSet.NOT then
            set_expression(context, operand_a, "not " .. get_expression(context, operand_b))
        
        elseif operation == InstructionSet.LEN then
            set_expression(context, operand_a, "#" .. get_expression(context, operand_b))
        
        elseif operation == InstructionSet.CONCAT then
            local concatenated_parts = {}
            for i = operand_b, operand_c do
                table.insert(concatenated_parts, get_expression(context, i))
            end
            set_expression(context, operand_a, table.concat(concatenated_parts, " .. "))
        
        elseif operation == InstructionSet.JMP then
        elseif operation == InstructionSet.EQ or operation == InstructionSet.LT or operation == InstructionSet.LE then
            local comparison_operator
            if operation == InstructionSet.EQ then
                comparison_operator = (operand_a ~= 0) and "~=" or "=="
            elseif operation == InstructionSet.LT then
                comparison_operator = (operand_a ~= 0) and ">=" or "<"
            else
                comparison_operator = (operand_a ~= 0) and ">" or "<="
            end
            output_line(context, "if " .. get_rk_value(context, operand_b) .. " " .. comparison_operator .. " " .. get_rk_value(context, operand_c) .. " then")
            context.indentation_level = context.indentation_level + 1
        
        elseif operation == InstructionSet.TEST then
            local condition = (operand_c == 0) and "not " .. get_expression(context, operand_a) or get_expression(context, operand_a)
            output_line(context, "if " .. condition .. " then")
            context.indentation_level = context.indentation_level + 1
        
        elseif operation == InstructionSet.TESTSET then
            local condition = (operand_c == 0) and "not " .. get_expression(context, operand_b) or get_expression(context, operand_b)
            set_expression(context, operand_a, get_expression(context, operand_b))
            output_line(context, "if " .. condition .. " then")
            context.indentation_level = context.indentation_level + 1
        
        elseif operation == InstructionSet.CALL then
            local function_expression
            local argument_list = {}
            
            if context.self_information then
                local self_data = context.self_information
                if self_data.method and valid_identifier(self_data.method) then
                    function_expression = self_data.object .. ":" .. self_data.method
                else
                    function_expression = self_data.object .. "[" .. self_data.method_raw .. "]"
                end
                
                if operand_b > 2 then
                    for i = operand_a + 2, operand_a + operand_b - 1 do
                        local arg_expr = get_expression(context, i)
                        if context.table_data[i] then
                            arg_expr = build_table_expression(context, i, context.indentation_level)
                            context.table_data[i] = nil
                        end
                        if context.pending_closures[i] then
                            arg_expr = context.pending_closures[i]
                            context.pending_closures[i] = nil
                        end
                        table.insert(argument_list, arg_expr)
                    end
                elseif operand_b == 0 then
                    local arg_expr = get_expression(context, operand_a + 1)
                    if arg_expr and arg_expr ~= generate_register_name(operand_a + 1, context.function_data.identifier) then
                        table.insert(argument_list, arg_expr)
                    end
                end
                context.self_information = nil
            else
                function_expression = get_expression(context, operand_a)
                if operand_b > 1 then
                    for i = operand_a + 1, operand_a + operand_b - 1 do
                        local arg_expr = get_expression(context, i)
                        if context.table_data[i] then
                            arg_expr = build_table_expression(context, i, context.indentation_level)
                            context.table_data[i] = nil
                        end
                        if context.pending_closures[i] then
                            arg_expr = context.pending_closures[i]
                            context.pending_closures[i] = nil
                        end
                        table.insert(argument_list, arg_expr)
                    end
                elseif operand_b == 0 then
                    local arg_expr = get_expression(context, operand_a + 1)
                    if arg_expr and arg_expr ~= generate_register_name(operand_a + 1, context.function_data.identifier) then
                        table.insert(argument_list, arg_expr)
                    end
                end
            end
            
            local function_call = function_expression .. "(" .. table.concat(argument_list, ", ") .. ")"
            
            if operand_c == 0 then
                set_expression(context, operand_a, function_call)
            elseif operand_c == 1 then
                output_line(context, function_call)
            elseif operand_c == 2 then
                local register_name = get_register_name(context, operand_a)
                if not context.declared_registers[operand_a] then
                    context.declared_registers[operand_a] = true
                    output_line(context, "local " .. register_name .. " = " .. function_call)
                else
                    output_line(context, register_name .. " = " .. function_call)
                end
                set_expression(context, operand_a, register_name)
                context.register_names[operand_a] = register_name
            else
                local return_values = {}
                for i = operand_a, operand_a + operand_c - 2 do
                    local reg_name = get_register_name(context, i)
                    table.insert(return_values, reg_name)
                    context.declared_registers[i] = true
                    set_expression(context, i, reg_name)
                    context.register_names[i] = reg_name
                end
                output_line(context, "local " .. table.concat(return_values, ", ") .. " = " .. function_call)
            end
        
        elseif operation == InstructionSet.TAILCALL then
            local function_expr = get_expression(context, operand_a)
            local tail_args = {}
            if operand_b > 1 then
                for i = operand_a + 1, operand_a + operand_b - 1 do
                    table.insert(tail_args, get_expression(context, i))
                end
            end
            output_line(context, "return " .. function_expr .. "(" .. table.concat(tail_args, ", ") .. ")")
        
        elseif operation == InstructionSet.RETURN then
            if operand_b == 1 then
                output_line(context, "return")
            elseif operand_b == 2 then
                output_line(context, "return " .. get_expression(context, operand_a))
            else
                local return_values = {}
                for i = operand_a, operand_a + operand_b - 2 do
                    table.insert(return_values, get_expression(context, i))
                end
                output_line(context, "return " .. table.concat(return_values, ", "))
            end
        
        elseif operation == InstructionSet.FORLOOP then
        elseif operation == InstructionSet.FORPREP then
            output_line(context, "for " .. get_register_name(context, operand_a + 3) .. " = " .. 
                       get_expression(context, operand_a) .. ", " .. 
                       get_expression(context, operand_a + 1) .. ", " .. 
                       get_expression(context, operand_a + 2) .. " do")
            context.indentation_level = context.indentation_level + 1
            context.declared_registers[operand_a + 3] = true
        
        elseif operation == InstructionSet.TFORLOOP then
            local iteration_vars = {}
            for i = operand_a + 3, operand_a + 2 + operand_c do
                table.insert(iteration_vars, get_register_name(context, i))
                context.declared_registers[i] = true
            end
            output_line(context, "for " .. table.concat(iteration_vars, ", ") .. " in " .. 
                       get_expression(context, operand_a) .. " do")
            context.indentation_level = context.indentation_level + 1
        
        elseif operation == InstructionSet.SETLIST then
            if context.table_data[operand_a] then
                for i = 1, operand_b do
                    table.insert(context.table_data[operand_a].array_entries, get_expression(context, operand_a + i))
                end
            end
        
        elseif operation == InstructionSet.CLOSURE then
            local function_prototype = function_data.children[extended_b + 1]
            local parameter_list = {}
            
            for i = 0, function_prototype.parameter_count - 1 do
                table.insert(parameter_list, generate_register_name(i, function_prototype.identifier))
            end
            
            if function_prototype.variable_arguments ~= 0 then
                table.insert(parameter_list, "...")
            end
            
            if can_inline_function(context, operand_a) then
                local inline_code = reconstruct_inline(context, function_prototype, context.indentation_level)
                context.pending_closures[operand_a] = inline_code
                set_expression(context, operand_a, inline_code)
            else
                local next_instruction = instructions[program_counter + 1]
                local named_function = next_instruction and next_instruction.opcode == InstructionSet.SETGLOBAL and next_instruction.a == operand_a
                local function_name = named_function and function_data.constants[next_instruction.bx + 1].value or nil
                
                if function_name and not valid_identifier(function_name) then
                    function_name = nil
                    named_function = false
                end
                
                if named_function then
                    output_line(context, "function " .. function_name .. "(" .. table.concat(parameter_list, ", ") .. ")")
                else
                    output_line(context, "local " .. get_register_name(context, operand_a) .. " = function(" .. table.concat(parameter_list, ", ") .. ")")
                    context.declared_registers[operand_a] = true
                end
                
                output_line(context, "  -- [" .. function_prototype.start_line .. ", " .. function_prototype.end_line .. "] func_id: " .. function_prototype.identifier)
                
                local child_context = create_context(function_prototype, context)
                child_context.indentation_level = context.indentation_level + 1
                reconstruct_function(child_context, function_prototype)
                
                for _, line in ipairs(child_context.output_lines) do
                    table.insert(context.output_lines, line)
                end
                
                output_line(context, "end")
                set_expression(context, operand_a, get_register_name(context, operand_a))
                
                if named_function then
                    program_counter = program_counter + 1
                end
            end
            program_counter = program_counter + function_prototype.upvalue_count
        
        elseif operation == InstructionSet.CLOSE then
        elseif operation == InstructionSet.VARARG then
            if operand_b == 0 then
                set_expression(context, operand_a, "...")
            else
                local varargs = {}
                for i = operand_a, operand_a + operand_b - 2 do
                    table.insert(varargs, get_register_name(context, i))
                    context.declared_registers[i] = true
                end
                output_line(context, "local " .. table.concat(varargs, ", ") .. " = ...")
            end
        
        else
            output_line(context, "-- UNSUPPORTED: " .. (InstructionNames[operation] or operation))
        end
        
        program_counter = program_counter + 1
    end
end

local input_file = io.open(bytecode_source, "rb")
if not input_file then
    io.stderr:write("Unable to open file: " .. bytecode_source .. "\n")
    os.exit(1)
end

local bytecode_data = input_file:read("*a")
input_file:close()

print("Processing bytecode: " .. bytecode_source)

local bytecode_processor = BytecodeProcessor:initialize(bytecode_data)
process_header(bytecode_processor)
local main_function = process_function(bytecode_processor, nil)

local reconstruction_context = create_context(main_function, nil)
table.insert(reconstruction_context.output_lines, "-- source: " .. (main_function.source_name or ""))
table.insert(reconstruction_context.output_lines, "-- version: lua51")
table.insert(reconstruction_context.output_lines, "-- lines: [" .. main_function.start_line .. ", " .. main_function.end_line .. "] id: " .. main_function.identifier)

local reconstruction_success, error_message = pcall(reconstruct_function, reconstruction_context, main_function)
if not reconstruction_success then
    io.stderr:write("Reconstruction failed: " .. tostring(error_message) .. "\n")
    os.exit(1)
end

local output_file = io.open(output_destination, "w")
if output_file then
    for _, line in ipairs(reconstruction_context.output_lines) do
        output_file:write(line .. "\n")
    end
    output_file:flush()
    output_file:close()
    print("Reconstruction saved to: " .. output_destination)
else
    io.stderr:write("Unable to write output: " .. output_destination .. "\n")
    os.exit(1)
end
