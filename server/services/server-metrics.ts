import os from "os";
import si from "systeminformation";

export interface ConnectionStats {
  active: number;
  connecting: number;
  disconnected: number;
  error: number;
  total: number;
}

export interface ServerMetrics {
  connections: ConnectionStats;
  server: {
    status: "healthy" | "warning" | "critical";
    cpuPercent: number;
    ramUsed: number;
    ramTotal: number;
    ramPercent: number;
    bandwidthIn: number;
    bandwidthOut: number;
    uptime: number;
    lastSampleAt: string;
  };
}

interface CachedMetrics {
  data: ServerMetrics | null;
  timestamp: number;
}

const CACHE_TTL = 5000; // 5 seconds
let metricsCache: CachedMetrics = { data: null, timestamp: 0 };

export class ServerMetricsService {
  /**
   * Get comprehensive server metrics with 5s cache
   */
  static async getMetrics(connectionStats: ConnectionStats): Promise<ServerMetrics> {
    const now = Date.now();
    
    // Return cached data if still valid
    if (metricsCache.data && (now - metricsCache.timestamp) < CACHE_TTL) {
      // Update connection stats (always fresh)
      metricsCache.data.connections = connectionStats;
      return metricsCache.data;
    }

    // Collect fresh metrics
    const [cpuData, memData, networkData] = await Promise.all([
      si.currentLoad(),
      si.mem(),
      si.networkStats()
    ]);

    const cpuPercent = Math.round(cpuData.currentLoad * 10) / 10;
    const ramUsed = Math.round(memData.used / (1024 ** 3) * 10) / 10; // GB
    const ramTotal = Math.round(memData.total / (1024 ** 3) * 10) / 10; // GB
    const ramPercent = Math.round((memData.used / memData.total) * 100);

    // Network stats (first interface, or sum if multiple)
    const network = networkData[0] || { rx_sec: 0, tx_sec: 0 };
    const bandwidthIn = Math.round(network.rx_sec / 1024); // KB/s
    const bandwidthOut = Math.round(network.tx_sec / 1024); // KB/s

    // System uptime
    const uptime = Math.round(os.uptime());

    // Determine server health status
    let status: "healthy" | "warning" | "critical" = "healthy";
    if (cpuPercent > 85 || ramPercent > 85) {
      status = "critical";
    } else if (cpuPercent > 60 || ramPercent > 60) {
      status = "warning";
    }

    const metrics: ServerMetrics = {
      connections: connectionStats,
      server: {
        status,
        cpuPercent,
        ramUsed,
        ramTotal,
        ramPercent,
        bandwidthIn,
        bandwidthOut,
        uptime,
        lastSampleAt: new Date().toISOString()
      }
    };

    // Update cache
    metricsCache = { data: metrics, timestamp: now };
    return metrics;
  }

  /**
   * Clear metrics cache (useful for testing)
   */
  static clearCache() {
    metricsCache = { data: null, timestamp: 0 };
  }
}
