import { app, BrowserWindow } from "electron";
import { spawn } from "child_process";

let mainWindow: BrowserWindow | null;
let pythonProcess: any;

app.on("ready", () => {
    pythonProcess = spawn("python", ["../../backend/app.py"]);

    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
        },
    });

    mainWindow.loadFile("../build/index.html");

    mainWindow.on("closed", () => {
        mainWindow = null;
        pythonProcess.kill();
    });
});
