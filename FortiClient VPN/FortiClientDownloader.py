#!/usr/local/autopkg/python
#
# Copyright 2024 Max Hewett
#

import subprocess
import re
import os
import signal
from autopkglib import Processor, ProcessorError

__all__ = ["FortiClientDownloader"]

class FortiClientDownloader(Processor):
    description = "Runs the FortiClientInstaller, monitors output, and stores the download path."
    input_variables = {
        "FORTICLIENT_EXECUTABLE": {
            "required": True,
            "description": "Path to the FortiClientInstaller executable.",
        }
    }
    output_variables = {
        "FORTICLIENT_DMG_PATH": {
            "description": "The path to the downloaded FortiClient DMG.",
        }
    }
    
    def run_executable(self):
        # Get the executable path from input variable
        executable_path = self.env.get("FORTICLIENT_EXECUTABLE")
        
        # Command to run the executable
        cmd = [executable_path]
        
        try:
            # Run the executable and capture output
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            
            # Monitor the output line by line
            for line in self.process.stdout:
                self.output(f"Output: {line.strip()}")  # Log the output
                
                # Regex to find the download path in the relevant output line
                match = re.search(r"Copy it to (\/\S+\.dmg)", line)
                if match:
                    self.env["FORTICLIENT_DMG_PATH"] = match.group(1)
                    self.output(f"Download path found: {self.env['FORTICLIENT_DMG_PATH']}")
                    
                    # Once the download path is found, terminate the process
                    self.terminate_process()
                    return True  # Path found, execution successful
                
            self.process.wait()
            
            # Suppress non-zero exit status if process was forcefully killed
            if self.process.returncode != 0 and self.process.returncode != -9:
                raise ProcessorError(f"Executable returned non-zero exit status {self.process.returncode}")
                
        except Exception as e:
            raise ProcessorError(f"Error running executable: {str(e)}")
            
        return False  # Path not found, execution unsuccessful
    
    def terminate_process(self):
        """Terminate the FortiClientInstaller process."""
        if self.process and self.process.poll() is None:
            self.output("Attempting to terminate FortiClientInstaller process...")
            self.process.terminate()
            
            # Wait a moment to check if it stopped
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.output("Termination taking too long, forcefully killing the process...")
                os.kill(self.process.pid, signal.SIGKILL)
                self.process.wait()
                
    def main(self):
        # Only raise an error if the download path was not found
        if not self.run_executable():
            raise ProcessorError("Failed to get download path.")
        else:
            self.output(f"Final download path: {self.env['FORTICLIENT_DMG_PATH']}")
            
            
if __name__ == "__main__":
    processor = FortiClientDownloader()
    processor.execute_shell()