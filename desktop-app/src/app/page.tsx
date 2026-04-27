"use client";

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileUp, FileText, CheckCircle2, Loader2, ArrowRight, X } from 'lucide-react';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isConverting, setIsConverting] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [isSuccess, setIsSuccess] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Setup Electron IPC Log Listener
  useEffect(() => {
    if (typeof window !== 'undefined' && (window as any).electronAPI) {
      (window as any).electronAPI.onConvertLog((msg: string) => {
        setLogs((prev) => [...prev, msg]);
      });
      return () => {
        (window as any).electronAPI.removeConvertLogListener();
      };
    }
  }, []);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.toLowerCase().endsWith('.pdf')) {
        setFile(droppedFile);
        setIsSuccess(false);
        setLogs([]);
      } else {
        alert("Please drop a valid .pdf file!");
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setIsSuccess(false);
      setLogs([]);
    }
  };

  const startConversion = async () => {
    if (!file) return;

    if (typeof window === 'undefined' || !(window as any).electronAPI) {
      alert("Electron API not found. Are you running this in the browser instead of the desktop app?");
      return;
    }

    try {
      // 1. Get original path (Electron exposes 'path' on the File object magically)
      const inputPath = (file as any).path;
      
      // 2. Generate default output path (same directory, just .md)
      const defaultOutputPath = inputPath.replace(/\.pdf$/i, '.md');

      // 3. Prompt user for save location
      const outputPath = await (window as any).electronAPI.showSaveDialog(defaultOutputPath);
      
      if (!outputPath) return; // User cancelled

      // 4. Start Conversion
      setIsConverting(true);
      setLogs(["Initializing Engine...", `Input: ${inputPath}`, `Output: ${outputPath}`]);

      const result = await (window as any).electronAPI.convertPDF(inputPath, outputPath);
      
      if (result.success) {
        setIsSuccess(true);
        setLogs((prev) => [...prev, "Conversion Complete!"]);
      } else {
        setLogs((prev) => [...prev, "ERROR: Conversion Failed.", result.error || "Unknown error."]);
      }
    } catch (error: any) {
      setLogs((prev) => [...prev, "CRITICAL ERROR:", error.toString()]);
    } finally {
      setIsConverting(false);
    }
  };

  const reset = () => {
    setFile(null);
    setIsSuccess(false);
    setLogs([]);
  };

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white font-sans flex flex-col items-center justify-center p-8 selection:bg-indigo-500/30">
      
      <div className="absolute top-0 w-full h-full overflow-hidden -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-indigo-600/20 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-purple-600/10 blur-[150px] rounded-full" />
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-12"
      >
        <h1 className="text-4xl font-bold tracking-tight mb-3 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
          PDF to Markdown Engine
        </h1>
        <p className="text-zinc-400 text-lg">Drop a structural PDF to extract highly semantic Markdown.</p>
      </motion.div>

      <div className="w-full max-w-2xl relative">
        <AnimatePresence mode="wait">
          {!file ? (
            <motion.div
              key="dropzone"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2 }}
            >
              <label 
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`flex flex-col items-center justify-center w-full h-80 rounded-3xl border-2 border-dashed transition-all duration-300 cursor-pointer group backdrop-blur-xl ${
                  isDragging 
                    ? "border-indigo-500 bg-indigo-500/10 shadow-[0_0_40px_rgba(99,102,241,0.2)]" 
                    : "border-zinc-800 bg-zinc-900/50 hover:bg-zinc-900/80 hover:border-zinc-700"
                }`}
              >
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <motion.div 
                    animate={{ y: isDragging ? -10 : 0 }}
                    className={`p-4 rounded-full mb-4 ${isDragging ? "bg-indigo-500/20 text-indigo-400" : "bg-zinc-800 text-zinc-400 group-hover:text-indigo-400 group-hover:bg-indigo-500/10 transition-colors"}`}
                  >
                    <FileUp size={32} />
                  </motion.div>
                  <p className="mb-2 text-xl font-medium text-zinc-300">
                    <span className="text-indigo-400 font-semibold">Click to upload</span> or drag and drop
                  </p>
                  <p className="text-sm text-zinc-500">Only structural PDF files are supported</p>
                </div>
                <input 
                  type="file" 
                  className="hidden" 
                  accept=".pdf"
                  onChange={handleFileSelect}
                />
              </label>
            </motion.div>
          ) : (
            <motion.div
              key="processing"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-zinc-900/60 backdrop-blur-2xl border border-zinc-800/50 rounded-3xl p-8 shadow-2xl"
            >
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center space-x-4">
                  <div className="w-14 h-14 bg-indigo-500/10 rounded-2xl flex items-center justify-center border border-indigo-500/20">
                    <FileText className="text-indigo-400" size={28} />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-zinc-200 truncate max-w-[300px]">
                      {file.name}
                    </h3>
                    <p className="text-zinc-500 text-sm">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                
                {!isConverting && !isSuccess && (
                  <button 
                    onClick={reset}
                    className="p-2 hover:bg-zinc-800 rounded-full text-zinc-400 hover:text-white transition-colors"
                  >
                    <X size={20} />
                  </button>
                )}
              </div>

              {!isConverting && !isSuccess && (
                <button
                  onClick={startConversion}
                  className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl font-medium text-lg transition-all duration-200 flex items-center justify-center group shadow-[0_0_20px_rgba(79,70,229,0.3)] hover:shadow-[0_0_30px_rgba(79,70,229,0.5)]"
                >
                  Convert to Markdown
                  <ArrowRight className="ml-2 group-hover:translate-x-1 transition-transform" size={20} />
                </button>
              )}

              {(isConverting || logs.length > 0) && (
                <div className="mt-6">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-zinc-400">Engine Output</span>
                    {isConverting && <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />}
                  </div>
                  <div className="bg-black/50 border border-zinc-800 rounded-xl p-4 h-48 overflow-y-auto font-mono text-xs text-zinc-300 shadow-inner space-y-1">
                    {logs.map((log, i) => (
                      <div key={i} className="break-words">{log}</div>
                    ))}
                    <div ref={logEndRef} />
                  </div>
                </div>
              )}

              {isSuccess && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-6 pt-6 border-t border-zinc-800/50 text-center"
                >
                  <div className="inline-flex items-center justify-center p-3 bg-emerald-500/10 text-emerald-400 rounded-full mb-3 border border-emerald-500/20">
                    <CheckCircle2 size={24} />
                  </div>
                  <h3 className="text-xl font-bold text-emerald-400 mb-1">Conversion Successful!</h3>
                  <p className="text-zinc-500 mb-6">Your beautifully structured Markdown file is ready.</p>
                  
                  <button
                    onClick={reset}
                    className="px-6 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl font-medium transition-colors"
                  >
                    Convert Another File
                  </button>
                </motion.div>
              )}

            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}
