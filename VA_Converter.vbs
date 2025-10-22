Option Explicit

Dim fso, shell, scriptDir, jsonFile, psScript
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
jsonFile = scriptDir & "\input.json"
psScript = scriptDir & "\AudioConverter.ps1"

Function GetUserInput()
    Dim data
    data = Array("", "", "", "")
    data(0) = Trim(InputBox("Enter YouTube video or playlist URL", "URL"))
    If data(0) = "" Then MsgBox "No URL entered. Exiting.", 48, "Aborted": WScript.Quit

    data(1) = Trim(InputBox("Enter folder name (e.g., album or artist)", "Folder"))
    If data(1) = "" Then MsgBox "No folder entered. Exiting.", 48, "Aborted": WScript.Quit

    data(2) = Trim(InputBox("Enter artist name (or leave blank)", "Artist"))
    data(3) = Trim(InputBox("Enter album name (or leave blank)", "Album"))
    
    GetUserInput = data
End Function

Function WriteJSON(url, folder, artist, album)
    Dim jsonText, file
    jsonText = "{""Url"": """ & url & """, " & _
                """FolderName"": """ & folder & """, " & _
                """Artist"": """ & artist & """, " & _
                """Album"": """ & album & """}"

    Set file = fso.CreateTextFile(jsonFile, True)
    file.WriteLine jsonText
    file.Close
End Function

Function DownloadAudio()
    Dim command, exitCode, data
    
    data = GetUserInput()
    WriteJSON data(0), data(1), data(2), data(3)

    command = "powershell -NoProfile -ExecutionPolicy Bypass -File """ & psScript & """ """ & jsonFile & """"
    exitCode = shell.Run(command, 0, True)

    If exitCode = 0 Then
        MsgBox "Download completed successfully!", 64, "Success"
    Else
        MsgBox "Conversion failed or encountered an error." & vbCrLf & _
           "Exit code: " & exitCode, vbCritical, "Error"
    End If
End Function

DownloadAudio