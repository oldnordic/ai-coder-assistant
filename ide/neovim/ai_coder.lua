-- AI Coder Assistant Neovim Plugin
-- Provides code analysis and security scanning integration

local M = {}

-- Configuration
M.config = {
    python_path = vim.fn.getenv('AI_CODER_PYTHON_PATH') or 'python',
    project_path = vim.fn.getenv('AI_CODER_PROJECT_PATH') or '',
    enable_auto_scan = false
}

-- Setup function
function M.setup(opts)
    M.config = vim.tbl_deep_extend('force', M.config, opts or {})
end

-- Commands
vim.api.nvim_create_user_command('AICoderScanFile', function()
    M.scan_current_file()
end, {})

vim.api.nvim_create_user_command('AICoderScanWorkspace', function()
    M.scan_workspace()
end, {})

vim.api.nvim_create_user_command('AICoderSecurityScan', function()
    M.security_scan()
end, {})

-- Key mappings
vim.keymap.set('n', '<leader>as', '<cmd>AICoderScanFile<CR>', { silent = true })
vim.keymap.set('n', '<leader>aw', '<cmd>AICoderScanWorkspace<CR>', { silent = true })
vim.keymap.set('n', '<leader>ass', '<cmd>AICoderSecurityScan<CR>', { silent = true })

-- Functions
function M.scan_current_file()
    if M.config.project_path == '' then
        vim.notify('Please set AI_CODER_PROJECT_PATH environment variable', vim.log.levels.ERROR)
        return
    end
    
    local file_path = vim.fn.expand('%:p')
    local language = M.get_language_from_extension(vim.fn.expand('%:e'))
    
    local command = string.format('%s -m src.cli.main analyze --file "%s" --language %s',
        M.config.python_path, file_path, language)
    
    vim.fn.jobstart({'sh', '-c', 'cd ' .. M.config.project_path .. ' && ' .. command}, {
        on_stdout = function(_, data)
            if data then
                M.display_results(table.concat(data, '\n'))
            end
        end,
        on_stderr = function(_, data)
            if data then
                vim.notify('AI Coder scan error: ' .. table.concat(data, '\n'), vim.log.levels.ERROR)
            end
        end
    })
end

function M.scan_workspace()
    if M.config.project_path == '' then
        vim.notify('Please set AI_CODER_PROJECT_PATH environment variable', vim.log.levels.ERROR)
        return
    end
    
    local workspace_path = vim.fn.getcwd()
    local command = string.format('%s -m src.cli.main scan "%s" --output /tmp/nvim_scan_results.json --format json',
        M.config.python_path, workspace_path)
    
    vim.fn.jobstart({'sh', '-c', 'cd ' .. M.config.project_path .. ' && ' .. command}, {
        on_exit = function()
            local file = io.open('/tmp/nvim_scan_results.json', 'r')
            if file then
                local content = file:read('*all')
                file:close()
                local results = vim.fn.json_decode(content)
                M.display_results(M.format_results(results))
            else
                vim.notify('Scan completed. Check output for results.', vim.log.levels.INFO)
            end
        end
    })
end

function M.security_scan()
    if M.config.project_path == '' then
        vim.notify('Please set AI_CODER_PROJECT_PATH environment variable', vim.log.levels.ERROR)
        return
    end
    
    local workspace_path = vim.fn.getcwd()
    local command = string.format('%s -m src.cli.main security-scan "%s" --output /tmp/nvim_security_results.json --format json',
        M.config.python_path, workspace_path)
    
    vim.fn.jobstart({'sh', '-c', 'cd ' .. M.config.project_path .. ' && ' .. command}, {
        on_exit = function()
            local file = io.open('/tmp/nvim_security_results.json', 'r')
            if file then
                local content = file:read('*all')
                file:close()
                local results = vim.fn.json_decode(content)
                M.display_results(M.format_security_results(results))
            else
                vim.notify('Security scan completed. Check output for results.', vim.log.levels.INFO)
            end
        end
    })
end

function M.get_language_from_extension(ext)
    local language_map = {
        py = 'python',
        js = 'javascript',
        ts = 'typescript',
        java = 'java',
        c = 'c',
        cpp = 'cpp',
        cs = 'csharp',
        go = 'go',
        rs = 'rust',
        php = 'php',
        rb = 'ruby',
        swift = 'swift',
        kt = 'kotlin',
        scala = 'scala',
        dart = 'dart',
        r = 'r',
        m = 'matlab',
        sh = 'shell',
        sql = 'sql',
        html = 'html'
    }
    return language_map[ext] or 'unknown'
end

function M.display_results(content)
    local buf = vim.api.nvim_create_buf(false, true)
    vim.api.nvim_buf_set_name(buf, '__AI_Coder_Results__')
    vim.api.nvim_buf_set_option(buf, 'buftype', 'nofile')
    vim.api.nvim_buf_set_option(buf, 'swapfile', false)
    vim.api.nvim_buf_set_option(buf, 'modifiable', true)
    
    local lines = vim.split(content, '\n')
    vim.api.nvim_buf_set_lines(buf, 0, -1, false, lines)
    vim.api.nvim_buf_set_option(buf, 'modifiable', false)
    
    vim.api.nvim_set_current_buf(buf)
end

function M.format_results(results)
    if not results or #results == 0 then
        return "✅ No issues found!"
    end
    
    local output = "AI Coder Assistant - Scan Results\n"
    output = output .. "Found " .. #results .. " issues\n\n"
    
    for _, result in ipairs(results) do
        output = output .. "File: " .. (result.file_path or 'unknown') .. ":" .. (result.line_number or 'unknown') .. "\n"
        output = output .. "Severity: " .. (result.severity or 'unknown') .. "\n"
        output = output .. "Type: " .. (result.issue_type or 'unknown') .. "\n"
        output = output .. "Description: " .. (result.description or 'No description') .. "\n"
        output = output .. "Suggestion: " .. (result.suggestion or 'No suggestion') .. "\n"
        output = output .. "---\n"
    end
    
    return output
end

function M.format_security_results(results)
    if not results or #results == 0 then
        return "✅ No security issues found!"
    end
    
    local output = "AI Coder Assistant - Security Scan Results\n"
    output = output .. "Found " .. #results .. " security issues\n\n"
    
    local critical_count = 0
    local high_count = 0
    
    for _, result in ipairs(results) do
        if result.severity == 'critical' then
            critical_count = critical_count + 1
        elseif result.severity == 'high' then
            high_count = high_count + 1
        end
    end
    
    output = output .. "Critical: " .. critical_count .. "\n"
    output = output .. "High: " .. high_count .. "\n\n"
    
    if critical_count > 0 then
        output = output .. "🚨 CRITICAL SECURITY ISSUES:\n"
        for _, result in ipairs(results) do
            if result.severity == 'critical' then
                output = output .. "• " .. (result.file_path or 'unknown') .. ":" .. (result.line_number or 'unknown') .. " - " .. (result.description or 'No description') .. "\n"
            end
        end
    end
    
    return output
end

return M 