"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Play, Download, Share2, Zap } from "lucide-react";

interface VideoPreviewModalProps {
    isOpen: boolean;
    onClose: () => void;
    videoUrl: string | null;
    title?: string;
}

export const VideoPreviewModal: React.FC<VideoPreviewModalProps> = ({ isOpen, onClose, videoUrl, title }) => {
    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-10 pointer-events-none"
            >
                <div className="absolute inset-0 bg-black/90 backdrop-blur-2xl pointer-events-auto" onClick={onClose} />

                <motion.div
                    initial={{ scale: 0.9, opacity: 0, y: 20 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.9, opacity: 0, y: 20 }}
                    transition={{ type: "spring", damping: 25, stiffness: 300 }}
                    className="relative w-full max-w-5xl aspect-video bg-zinc-950 rounded-[2.5rem] border border-white/10 overflow-hidden shadow-[0_0_100px_rgba(0,0,0,0.8)] pointer-events-auto"
                >
                    {/* Header */}
                    <div className="absolute top-0 inset-x-0 p-8 flex items-center justify-between z-20 bg-gradient-to-b from-black/80 to-transparent">
                        <div className="space-y-1">
                            <div className="flex items-center gap-3">
                                <div className="h-1 w-6 bg-primary rounded-full" />
                                <span className="text-[10px] font-black tracking-[0.3em] text-primary uppercase">Outcome Preview</span>
                            </div>
                            <h2 className="text-2xl font-black text-white uppercase italic tracking-tighter truncate max-w-md">
                                {title || "Untitled Viral Fragment"}
                            </h2>
                        </div>
                        <button
                            onClick={onClose}
                            className="h-12 w-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-white hover:bg-white/10 hover:border-white/20 transition-all"
                        >
                            <X className="h-6 w-6" />
                        </button>
                    </div>

                    {/* Video Content */}
                    <div className="absolute inset-0 flex items-center justify-center bg-black">
                        {videoUrl ? (
                            <video
                                src={videoUrl}
                                className="h-full w-full object-contain"
                                controls
                                autoPlay
                            />
                        ) : (
                            <div className="flex flex-col items-center gap-4">
                                <Zap className="h-12 w-12 text-primary animate-pulse" />
                                <p className="text-xs font-black uppercase tracking-widest text-zinc-500">Reticulating Splines...</p>
                            </div>
                        )}
                    </div>

                    {/* Controls/Actions Overlay */}
                    <div className="absolute bottom-0 inset-x-0 p-8 flex items-center justify-between z-20 bg-gradient-to-t from-black/80 to-transparent">
                        <div className="flex items-center gap-4">
                            <button className="flex items-center gap-3 bg-white text-black px-6 py-3 rounded-2xl font-black uppercase text-[10px] tracking-widest hover:scale-105 transition-all">
                                <Play className="h-4 w-4 fill-black" />
                                Play Original
                            </button>
                            <button className="flex items-center gap-3 bg-zinc-900 text-white px-6 py-3 rounded-2xl font-black uppercase text-[10px] tracking-widest border border-white/5 hover:border-white/20 transition-all">
                                <Download className="h-4 w-4" />
                                Export
                            </button>
                        </div>

                        <div className="hidden md:flex items-center gap-10">
                            <div className="text-right">
                                <p className="text-[9px] font-black text-zinc-500 uppercase tracking-widest mb-1">Status</p>
                                <p className="text-xs font-black text-emerald-500 uppercase italic">Ready to Publish</p>
                            </div>
                            <button className="h-14 w-14 rounded-2xl bg-primary text-black flex items-center justify-center shadow-[0_0_30px_rgba(var(--primary-rgb),0.3)] hover:scale-110 transition-all">
                                <Share2 className="h-6 w-6" />
                            </button>
                        </div>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
};
