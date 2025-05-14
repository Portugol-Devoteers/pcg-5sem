import { app, BrowserWindow } from "electron";
import { spawn } from "child_process";

let mainWindow: BrowserWindow | null;
let pythonProcess: any;

app.on("ready", () => {
    pythonProcess = spawn("python", ["../../backend/app.py"]);

    mainWindow = new BrowserWindow({
        width: 816,
        height: 700,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
        },
    });

    // mainWindow.loadFile("../build/index.html"); // Uncomment this line to load the React app from build folder
    mainWindow.loadURL("http://localhost:3000");

    mainWindow.on("closed", () => {
        mainWindow = null;
        pythonProcess.kill();
    });
});
