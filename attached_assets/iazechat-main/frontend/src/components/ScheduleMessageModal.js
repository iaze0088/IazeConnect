import React, { useState } from 'react';
import { Calendar, Clock, Send } from 'lucide-react';

const ScheduleMessageModal = ({ ticket, onClose, onSchedule }) => {
  const [message, setMessage] = useState('');
  const [scheduleType, setScheduleType] = useState('relative'); // 'relative' ou 'datetime'
  const [datetime, setDatetime] = useState('');
  const [hours, setHours] = useState(0);
  const [minutes, setMinutes] = useState(30);
  const [loading, setLoading] = useState(false);

  const handleSchedule = async () => {
    if (!message.trim()) {
      alert('Digite uma mensagem');
      return;
    }

    if (scheduleType === 'datetime' && !datetime) {
      alert('Selecione data e hora');
      return;
    }

    if (scheduleType === 'relative' && hours === 0 && minutes === 0) {
      alert('Defina o tempo de espera');
      return;
    }

    setLoading(true);

    try {
      const requestData = {
        ticket_id: ticket.id,
        message: message,
        schedule_type: scheduleType
      };

      if (scheduleType === 'datetime') {
        requestData.datetime = datetime;
      } else {
        requestData.hours = hours;
        requestData.minutes = minutes;
      }

      await onSchedule(requestData);
      
      alert('Mensagem agendada com sucesso!');
      onClose();
    } catch (error) {
      console.error('Erro ao agendar:', error);
      alert('Erro ao agendar mensagem');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl p-6">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <Clock className="w-6 h-6 text-blue-600" />
          Agendar Mensagem
        </h2>

        {/* Cliente info */}
        <div className="mb-4 p-3 bg-gray-100 rounded">
          <p className="text-sm text-gray-600">Cliente:</p>
          <p className="font-semibold">{ticket.client_name || ticket.whatsapp}</p>
        </div>

        {/* Tipo de agendamento */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Tipo de Agendamento</label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="radio"
                value="relative"
                checked={scheduleType === 'relative'}
                onChange={(e) => setScheduleType(e.target.value)}
                className="mr-2"
              />
              Tempo Relativo (daqui X tempo)
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="datetime"
                checked={scheduleType === 'datetime'}
                onChange={(e) => setScheduleType(e.target.value)}
                className="mr-2"
              />
              Data/Hora Específica
            </label>
          </div>
        </div>

        {/* Campos de agendamento */}
        {scheduleType === 'relative' ? (
          <div className="mb-4 grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Horas</label>
              <input
                type="number"
                min="0"
                max="48"
                value={hours}
                onChange={(e) => setHours(parseInt(e.target.value) || 0)}
                className="w-full px-3 py-2 border rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Minutos</label>
              <input
                type="number"
                min="0"
                max="59"
                value={minutes}
                onChange={(e) => setMinutes(parseInt(e.target.value) || 0)}
                className="w-full px-3 py-2 border rounded"
              />
            </div>
            <div className="col-span-2 text-sm text-gray-600">
              Será enviada em: {hours}h {minutes}min
            </div>
          </div>
        ) : (
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Data e Hora</label>
            <input
              type="datetime-local"
              value={datetime}
              onChange={(e) => setDatetime(e.target.value)}
              className="w-full px-3 py-2 border rounded"
              min={new Date().toISOString().slice(0, 16)}
            />
          </div>
        )}

        {/* Mensagem */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Mensagem</label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Digite a mensagem que será enviada..."
            rows="5"
            className="w-full px-3 py-2 border rounded resize-none"
          />
        </div>

        {/* Botões */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded hover:bg-gray-100"
            disabled={loading}
          >
            Cancelar
          </button>
          <button
            onClick={handleSchedule}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2"
            disabled={loading}
          >
            <Send className="w-4 h-4" />
            {loading ? 'Agendando...' : 'Agendar Mensagem'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ScheduleMessageModal;
