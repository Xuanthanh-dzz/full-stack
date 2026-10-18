namespace CommerceLab.Data.Entities;

public sealed class Customer
{
    public long CustomerId { get; set; }

    public required string Email { get; set; }

    public required string FullName { get; set; }

    public DateTime CreatedAt { get; set; }

    public List<Order> Orders { get; } = [];
}
