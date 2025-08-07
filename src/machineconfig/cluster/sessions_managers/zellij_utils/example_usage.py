#!/usr/bin/env python3
"""
Example usage of the modularized Zellij remote layout generator.
"""

from machineconfig.cluster.sessions_managers.zellij_remote import ZellijRemoteLayoutGenerator

def example_usage():
    """Demonstrate the refactored modular usage."""
    
    # Sample tab configuration
    sample_tabs = {
        "🤖Bot1": ("~/code/bytesense/bithence", "~/scripts/fire -mO go1.py bot1 --kw create_new_bot True"),
        "🤖Bot2": ("~/code/bytesense/bithence", "~/scripts/fire -mO go2.py bot2 --kw create_new_bot True"), 
        "📊Monitor": ("~", "htop"),
        "📝Logs": ("/var/log", "tail -f /var/log/app.log")
    }
    
    # Replace 'myserver' with an actual SSH config alias
    remote_name = "myserver"  # This should be in ~/.ssh/config
    session_name = "test_remote_session"
    
    try:
        # Create layout using the remote generator
        generator = ZellijRemoteLayoutGenerator(remote_name=remote_name, session_name_prefix=session_name)
        
        # Create layout file
        layout_path = generator.create_zellij_layout(sample_tabs)
        print(f"✅ Remote layout created successfully: {layout_path}")
        
        # Preview the layout content
        preview = generator.get_layout_preview(sample_tabs)
        print(f"📄 Layout preview:\n{preview}")
        
        # Check status using the modular components
        print(f"\n🔍 Checking command status on remote '{remote_name}':")
        generator.print_status_report()
        
        # The individual components can also be used directly:
        print(f"\n🔧 Direct component usage examples:")
        
        # Use remote executor directly
        print(f"Remote executor: {generator.remote_executor.remote_name}")
        
        # Use layout generator directly  
        layout_content = generator.layout_generator.generate_layout_content(sample_tabs)
        print(f"Layout content length: {len(layout_content)} characters")
        
        # Use process monitor directly
        status = generator.process_monitor.check_all_commands_status(sample_tabs)
        print(f"Command status check completed for {len(status)} commands")
        
        print("\n✅ All modular components working correctly!")
        
        # Uncomment these to actually start and attach to the session:
        # start_result = generator.start_zellij_session()
        # print(f"Session start result: {start_result}")
        # generator.attach_to_session()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    example_usage()
