namespace CommerceLab.Data.Entities;

public sealed class Payment
{
    public long PaymentId { get; set; }

    public long OrderId { get; set; }

    public Order Order { get; set; } = null!;

    public required string Provider { get; set; }

    public string? ProviderReference { get; set; }

    public required string Status { get; set; }

    public decimal Amount { get; set; }

    public DateTime CreatedAt { get; set; }
}
