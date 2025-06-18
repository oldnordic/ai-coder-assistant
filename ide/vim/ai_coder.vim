" AI Coder Assistant Vim Plugin
" Provides code analysis and security scanning integration

if exists('g:loaded_ai_coder')
    finish
endif
let g:loaded_ai_coder = 1

" Configuration
let g:ai_coder_python_path = get(g:, 'ai_coder_python_path', 'python')
let g:ai_coder_project_path = get(g:, 'ai_coder_project_path', '')
let g:ai_coder_enable_auto_scan = get(g:, 'ai_coder_enable_auto_scan', 0)

" Commands
command! -nargs=0 AICoderScanFile call s:scan_current_file()
command! -nargs=0 AICoderScanWorkspace call s:scan_workspace()
command! -nargs=0 AICoderSecurityScan call s:security_scan()

" Key mappings
nnoremap <silent> <leader>as :AICoderScanFile<CR>
nnoremap <silent> <leader>aw :AICoderScanWorkspace<CR>
nnoremap <silent> <leader>ass :AICoderSecurityScan<CR>

" Functions
function! s:scan_current_file()
    if empty(g:ai_coder_project_path)
        echoerr "Please set g:ai_coder_project_path"
        return
    endif
    
    let file_path = expand('%:p')
    let language = s:get_language_from_extension(expand('%:e'))
    
    let command = g:ai_coder_python_path . ' -m src.cli.main analyze --file "' . file_path . '" --language ' . language
    let output = system('cd ' . g:ai_coder_project_path . ' && ' . command)
    
    call s:display_results(output)
endfunction

function! s:scan_workspace()
    if empty(g:ai_coder_project_path)
        echoerr "Please set g:ai_coder_project_path"
        return
    endif
    
    let workspace_path = getcwd()
    let command = g:ai_coder_python_path . ' -m src.cli.main scan "' . workspace_path . '" --output /tmp/vim_scan_results.json --format json'
    let output = system('cd ' . g:ai_coder_project_path . ' && ' . command)
    
    if filereadable('/tmp/vim_scan_results.json')
        let results = json_decode(readfile('/tmp/vim_scan_results.json'))
        call s:display_results(s:format_results(results))
    else
        echo "Scan completed. Check output for results."
    endif
endfunction

function! s:security_scan()
    if empty(g:ai_coder_project_path)
        echoerr "Please set g:ai_coder_project_path"
        return
    endif
    
    let workspace_path = getcwd()
    let command = g:ai_coder_python_path . ' -m src.cli.main security-scan "' . workspace_path . '" --output /tmp/vim_security_results.json --format json'
    let output = system('cd ' . g:ai_coder_project_path . ' && ' . command)
    
    if filereadable('/tmp/vim_security_results.json')
        let results = json_decode(readfile('/tmp/vim_security_results.json'))
        call s:display_results(s:format_security_results(results))
    else
        echo "Security scan completed. Check output for results."
    endif
endfunction

function! s:get_language_from_extension(ext)
    let language_map = {
        \ 'py': 'python',
        \ 'js': 'javascript',
        \ 'ts': 'typescript',
        \ 'java': 'java',
        \ 'c': 'c',
        \ 'cpp': 'cpp',
        \ 'cs': 'csharp',
        \ 'go': 'go',
        \ 'rs': 'rust',
        \ 'php': 'php',
        \ 'rb': 'ruby',
        \ 'swift': 'swift',
        \ 'kt': 'kotlin',
        \ 'scala': 'scala',
        \ 'dart': 'dart',
        \ 'r': 'r',
        \ 'm': 'matlab',
        \ 'sh': 'shell',
        \ 'sql': 'sql',
        \ 'html': 'html'
        \ }
    return get(language_map, a:ext, 'unknown')
endfunction

function! s:display_results(content)
    " Create a new buffer to display results
    let buf = bufnr('__AI_Coder_Results__', 1)
    call setbufvar(buf, '&buftype', 'nofile')
    call setbufvar(buf, '&swapfile', 0)
    call setbufvar(buf, '&modifiable', 1)
    
    call setbufline(buf, 1, split(a:content, '\n'))
    call setbufvar(buf, '&modifiable', 0)
    
    execute 'buffer ' . buf
endfunction

function! s:format_results(results)
    if empty(a:results)
        return "✅ No issues found!"
    endif
    
    let output = "AI Coder Assistant - Scan Results\n"
    let output .= "Found " . len(a:results) . " issues\n\n"
    
    for result in a:results
        let output .= "File: " . result.file_path . ":" . result.line_number . "\n"
        let output .= "Severity: " . result.severity . "\n"
        let output .= "Type: " . result.issue_type . "\n"
        let output .= "Description: " . result.description . "\n"
        let output .= "Suggestion: " . result.suggestion . "\n"
        let output .= "---\n"
    endfor
    
    return output
endfunction

function! s:format_security_results(results)
    if empty(a:results)
        return "✅ No security issues found!"
    endif
    
    let output = "AI Coder Assistant - Security Scan Results\n"
    let output .= "Found " . len(a:results) . " security issues\n\n"
    
    let critical_count = 0
    let high_count = 0
    
    for result in a:results
        if result.severity == 'critical'
            let critical_count += 1
        elseif result.severity == 'high'
            let high_count += 1
        endif
    endfor
    
    let output .= "Critical: " . critical_count . "\n"
    let output .= "High: " . high_count . "\n\n"
    
    if critical_count > 0
        let output .= "🚨 CRITICAL SECURITY ISSUES:\n"
        for result in a:results
            if result.severity == 'critical'
                let output .= "• " . result.file_path . ":" . result.line_number . " - " . result.description . "\n"
            endif
        endfor
    endif
    
    return output
endfunction 