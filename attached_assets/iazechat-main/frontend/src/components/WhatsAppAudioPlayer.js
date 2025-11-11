import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause } from 'lucide-react';

const WhatsAppAudioPlayer = ({ src, isSentByMe = false }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => setDuration(audio.duration);
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('timeupdate', updateTime);
    audio.addEventListener('loadedmetadata', updateDuration);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', updateTime);
      audio.removeEventListener('loadedmetadata', updateDuration);
      audio.removeEventListener('ended', handleEnded);
    };
  }, []);

  const togglePlay = () => {
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    audioRef.current.currentTime = percentage * duration;
  };

  const formatTime = (time) => {
    if (!time || isNaN(time)) return '0:00';
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const progress = duration ? (currentTime / duration) * 100 : 0;

  return (
    <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg ${isSentByMe ? 'bg-transparent' : 'bg-transparent'} w-full max-w-[250px]`}>
      {/* Botão Play/Pause - Menor */}
      <button
        onClick={togglePlay}
        className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-all ${
          isSentByMe 
            ? 'bg-green-600 hover:bg-green-700' 
            : 'bg-teal-500 hover:bg-teal-600'
        } text-white`}
      >
        {isPlaying ? (
          <Pause className="w-3 h-3" fill="white" />
        ) : (
          <Play className="w-3 h-3 ml-0.5" fill="white" />
        )}
      </button>

      {/* Waveform - Compacto */}
      <div 
        className="flex-1 min-w-0 flex items-center gap-[1.5px] h-6 cursor-pointer overflow-hidden"
        onClick={handleSeek}
      >
        {[...Array(35)].map((_, i) => {
          const baseHeight = Math.abs(Math.sin(i * 0.3)) * 16 + 6;
          const noise = Math.sin(i * 1.5) * 2;
          const height = Math.min(22, baseHeight + noise);
          const isPlayed = (i / 35) * 100 < progress;
          
          return (
            <div
              key={i}
              className={`transition-all duration-100 ${
                isPlayed 
                  ? (isSentByMe ? 'bg-green-700' : 'bg-teal-600')
                  : 'bg-gray-300'
              } rounded-full`}
              style={{ 
                height: `${height}px`,
                width: '2.5px',
                flexShrink: 0
              }}
            />
          );
        })}
      </div>

      {/* Duração - Compacta */}
      <div className={`text-[10px] font-medium ${isSentByMe ? 'text-green-800' : 'text-gray-600'} min-w-[28px] text-right flex-shrink-0`}>
        {formatTime(duration - currentTime)}
      </div>

      {/* Áudio invisível */}
      <audio ref={audioRef} src={src} preload="metadata" />
    </div>
  );
};

export default WhatsAppAudioPlayer;
