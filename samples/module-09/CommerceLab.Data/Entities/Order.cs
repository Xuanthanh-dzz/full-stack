namespace CommerceLab.Data.Entities;

public sealed class Order
{
    public long OrderId { get; set; }

    public long CustomerId { get; set; }

    public Customer Customer { get; set; } = null!;

    public required string Status { get; set; }

    public required string ShippingName { get; set; }

    public required string ShippingAddress { get; set; }

    public decimal TotalAmount { get; set; }

    public DateTime OrderedAt { get; set; }

    public Guid ConcurrencyToken { get; set; }

    public List<OrderItem> Items { get; } = [];

    public List<Payment> Payments { get; } = [];
}
