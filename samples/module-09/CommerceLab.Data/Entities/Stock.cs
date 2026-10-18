namespace CommerceLab.Data.Entities;

public sealed class Stock
{
    public long ProductId { get; set; }

    public Product Product { get; set; } = null!;

    public int Quantity { get; set; }
}
