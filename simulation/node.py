import random
from typing import List, Optional, Tuple

class Node:
    """
    Ağdaki tek bir düğümü (cihazı) temsil eden sınıf.
    Her düğüm afet durumlarında iletişim kurabilen bir cihazdır.
    """
    
    def __init__(self, node_id: int, position: Tuple[float, float]):
        """
        Node sınıfı başlatıcı
        
        Args:
            node_id: Düğümün benzersiz kimliği
            position: (x, y) koordinatları
        """
        self.id = node_id
        self.position = position  # (x, y) koordinatları
        self.is_active = True     # Düğüm aktif/pasif durumu
        self.buffer = []          # Gelen paketlerin kuyruğu
        self.neighbors = []       # Komşu düğümlerin ID listesi
        self.energy = 100.0       # Enerji seviyesi (0-100)
        
    def send_packet(self, packet, neighbor_id: int = None):
        """
        Paket gönderme fonksiyonu
        
        Args:
            packet: Gönderilecek paket
            neighbor_id: Hedef komşu ID (None ise rastgele seç)
        """
        if not self.is_active:
            print(f"Node {self.id}: Pasif durumda, paket gönderilemiyor!")
            return False
            
        if not self.neighbors:
            print(f"Node {self.id}: Komşu bulunamadı!")
            return False
            
        # Hedef komşu seçimi
        if neighbor_id is None:
            target = random.choice(self.neighbors)
        else:
            target = neighbor_id
            
        print(f"Node {self.id}: Paket gönderiliyor -> Node {target}")
        return True
    
    def receive_packet(self, packet):
        """
        Paket alma fonksiyonu
        
        Args:
            packet: Gelen paket
        """
        if not self.is_active:
            print(f"Node {self.id}: Pasif durumda, paket alınamıyor!")
            return False
            
        self.buffer.append(packet)
        print(f"Node {self.id}: Paket alındı. Buffer size: {len(self.buffer)}")
        return True
    
    def fail(self):
        """Düğümü arızalı/pasif duruma geçir"""
        self.is_active = False
        print(f"Node {self.id}: ARIZALI! Koordinat: {self.position}")
    
    def repair(self):
        """Düğümü tekrar aktif duruma getir"""
        self.is_active = True
        print(f"Node {self.id}: TAMİR EDİLDİ! Koordinat: {self.position}")
    
    def add_neighbor(self, neighbor_id: int):
        """Komşu düğüm ekle"""
        if neighbor_id not in self.neighbors:
            self.neighbors.append(neighbor_id)
    
    def remove_neighbor(self, neighbor_id: int):
        """Komşu düğüm çıkar"""
        if neighbor_id in self.neighbors:
            self.neighbors.remove(neighbor_id)
    
    def get_status(self) -> dict:
        """Düğüm durumu bilgilerini döndür"""
        return {
            'id': self.id,
            'position': self.position,
            'is_active': self.is_active,
            'buffer_size': len(self.buffer),
            'neighbors': self.neighbors,
            'energy': self.energy
        }
    
    def __str__(self):
        status = "AKTİF" if self.is_active else "PASİF"
        return f"Node {self.id}: {self.position} - {status} - {len(self.neighbors)} komşu"

# Test fonksiyonu
def test_node():
    """Node sınıfının temel test fonksiyonu"""
    print("=== NODE SINIFI TEST ===")
    
    # Node oluştur
    node1 = Node(1, (10.0, 20.0))
    node2 = Node(2, (15.0, 25.0))
    
    print(f"Node 1: {node1}")
    print(f"Node 2: {node2}")
    
    # Komşu ekle
    node1.add_neighbor(2)
    node2.add_neighbor(1)
    
    print(f"\nKomşu eklendikten sonra:")
    print(f"Node 1 komşuları: {node1.neighbors}")
    print(f"Node 2 komşuları: {node2.neighbors}")
    
    # Paket gönder
    print(f"\nPaket gönderimi:")
    node1.send_packet("Merhaba dünya!")
    
    # Node arızası simülasyonu
    print(f"\nNode arızası simülasyonu:")
    node1.fail()
    node1.send_packet("Bu paket gönderilmeyecek")
    
    # Node tamiri
    print(f"\nNode tamiri:")
    node1.repair()
    node1.send_packet("Bu paket gönderilecek!")
    
    # Status bilgileri
    print(f"\nNode durumları:")
    print(f"Node 1 status: {node1.get_status()}")
    print(f"Node 2 status: {node2.get_status()}")

if __name__ == "__main__":
    test_node()