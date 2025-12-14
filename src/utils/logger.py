"""
Network Logger Module
Ağ simülasyonu ve AI eğitimi için yapılandırılabilir logging sistemi
"""

import logging
import os
from datetime import datetime
from typing import Optional


class NetworkLogger:
    """
    Network simülasyonu için özelleştirilmiş logger sınıfı

    Log seviyeleri:
    - DEBUG: Detaylı debugging bilgileri
    - INFO: Genel bilgi mesajları
    - WARNING: Uyarı mesajları
    - ERROR: Hata mesajları
    - CRITICAL: Kritik hatalar
    """

    def __init__(
        self,
        name: str = "LifeNode",
        level: int = logging.INFO,
        log_to_file: bool = True,
        log_dir: str = "logs",
    ):
        """
        Args:
            name: Logger ismi
            level: Minimum log seviyesi (logging.DEBUG, INFO, WARNING, vb.)
            log_to_file: Dosyaya log yazılsın mı
            log_dir: Log dosyalarının kaydedileceği dizin
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers = []  # Mevcut handler'ları temizle

        # Formatter oluştur
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler (opsiyonel)
        if log_to_file:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            self.logger.info(f"Log dosyası oluşturuldu: {log_file}")

    def debug(self, message: str):
        """Debug seviyesinde log"""
        self.logger.debug(message)

    def info(self, message: str):
        """Info seviyesinde log"""
        self.logger.info(message)

    def warning(self, message: str):
        """Warning seviyesinde log"""
        self.logger.warning(message)

    def error(self, message: str):
        """Error seviyesinde log"""
        self.logger.error(message)

    def critical(self, message: str):
        """Critical seviyesinde log"""
        self.logger.critical(message)

    def log_network_event(
        self,
        event_type: str,
        node_id: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        """
        Network olaylarını logla

        Args:
            event_type: Olay tipi (packet_sent, node_failure, routing, vb.)
            node_id: İlgili node ID (varsa)
            details: Ek detaylar
        """
        msg = f"[{event_type.upper()}]"
        if node_id is not None:
            msg += f" Node {node_id}"
        if details:
            msg += f" | {details}"

        self.info(msg)

    def log_training_step(self, episode: int, step: int, reward: float, success: bool):
        """
        AI eğitim adımlarını logla

        Args:
            episode: Episode numarası
            step: Adım numarası
            reward: Alınan ödül
            success: Başarılı mı
        """
        status = "SUCCESS" if success else "FAILURE"
        msg = (
            f"[TRAINING] Episode {episode:3d} | "
            f"Step {step:3d} | "
            f"Reward {reward:7.2f} | "
            f"{status}"
        )
        self.info(msg)

    def log_network_stats(self, stats: dict):
        """
        Ağ istatistiklerini logla

        Args:
            stats: Network.get_network_stats() çıktısı
        """
        msg = "[STATS] "
        msg += " | ".join([f"{k}: {v}" for k, v in stats.items()])
        self.info(msg)

    def set_level(self, level: int):
        """Log seviyesini değiştir"""
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)


# Global logger instance'ı
_global_logger: Optional[NetworkLogger] = None


def get_logger(
    name: str = "LifeNode",
    level: int = logging.INFO,
    log_to_file: bool = False,
) -> NetworkLogger:
    """
    Global logger instance'ı al veya oluştur

    Args:
        name: Logger ismi
        level: Log seviyesi
        log_to_file: Dosyaya log yazılsın mı

    Returns:
        NetworkLogger instance
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = NetworkLogger(name=name, level=level, log_to_file=log_to_file)

    return _global_logger
