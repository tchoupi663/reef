from nicegui import ui
import asyncio
import subprocess

def page_header(title: str, subtitle: str = None):
    with ui.column().classes('w-full mb-6'):
        ui.label(title).classes('text-3xl font-bold text-white tracking-tight')
        if subtitle:
            ui.label(subtitle).classes('text-lg text-slate-400')
    ui.separator().classes('mb-6 bg-slate-700')

def card_style():
    return 'p-6 rounded-2xl bg-white/5 border border-white/10 shadow-lg backdrop-blur-md transition-all hover:-translate-y-1 hover:shadow-2xl'

async def async_run_command(command: str, log_element: ui.log, on_complete=None):
    """
    Asynchronously run a shell command and stream output to a UI log element.
    """
    log_element.push(f"Running: {command}")
    
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        executable='/bin/zsh'
    )

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        text = line.decode().strip()
        log_element.push(text)

    await process.wait()
    
    if process.returncode == 0:
        ui.notify('Command completed successfully', type='positive')
    else:
        ui.notify(f'Command failed with exit code {process.returncode}', type='negative')

    if on_complete:
        on_complete(process.returncode)

def status_badge(active: bool, text_active="Active", text_inactive="Inactive"):
    color = "green-400" if active else "amber-400"
    text = text_active if active else text_inactive
    
    with ui.row().classes('items-center gap-2'):
        ui.icon('circle', size='xs').classes(f'text-{color}')
        ui.label(text).classes(f'text-{color} font-bold')
