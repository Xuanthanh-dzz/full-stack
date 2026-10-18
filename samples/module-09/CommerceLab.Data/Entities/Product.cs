namespace CommerceLab.Data.Entities;

public sealed class Product
{
    public long ProductId { get; set; }

    public required string Sku { get; set; }

    public required string Name { get; set; }

    public decimal Price { get; set; }

    public bool IsActive { get; set; } = true;

    public DateTime CreatedAt { get; set; }

    public List<OrderItem> OrderItems { get; } = [];
}
