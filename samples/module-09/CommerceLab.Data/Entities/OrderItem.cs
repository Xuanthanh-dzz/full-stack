namespace CommerceLab.Data.Entities;

public sealed class OrderItem
{
    public long OrderItemId { get; set; }

    public long OrderId { get; set; }

    public Order Order { get; set; } = null!;

    public long ProductId { get; set; }

    public Product Product { get; set; } = null!;

    public required string ProductNameSnapshot { get; set; }

    public decimal UnitPriceSnapshot { get; set; }

    public int Quantity { get; set; }
}
