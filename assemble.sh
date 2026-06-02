#!/bin/bash
read_files_recursive() {
    # Loop through everything in the directory
    for item in "$1"/*; do
        if [ -d "$item" ]; then
            # If it's a directory, go deeper
            read_files_recursive "$item"
        elif [ -f "$item" ]; then
            ext="${item##*.}"
            language=''
            if [ "$ext" == "py" ]; then
                language="python"
            elif [ "$ext" == "sh" ]; then
                language="bash"
            elif [ "$ext" == "html" ]; then
                language="html"
            elif [ "$ext" == "js" ]; then
                language="javascript"
            elif [ "$ext" == "" ]; then
                language="bash"
            fi
            if [[ "$ext" != "pyc" && "$ext" != "pb" && "$ext" != "h5" && "$ext" != "xml" && "$ext" != "pt" && "$ext" != "zip" && "$ext" != "onnx" && "$ext" != "ipqs" ]]; then
                # If it's a file, print the name and content
                echo "--- File: $item ---"
                echo $"\`\`\`$language"
                cat "$item"
                echo "\`\`\`"
                echo -e "\n"
            fi
        fi
    done
}

# Example usage:
read_files_recursive "$1"
