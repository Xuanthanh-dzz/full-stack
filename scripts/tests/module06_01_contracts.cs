using OrderModelingDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static void Main(){

 var c=new Customer(" a ","Name");var o=new Order("o",c,"vnd");var view=o.Lines;
 Throws<InvalidOperationException>(()=>o.Place());Check(o.Status==OrderStatus.Draft,"empty stays draft");
 o.AddLine(new OrderLine("x",2,Money.Vnd(3)));Check(view.Count==1 && o.Total==Money.Vnd(6),"live view and total");
 Check(view is not List<OrderLine>,"do not leak list");Throws<NotSupportedException>(()=>((ICollection<OrderLine>)view).Clear());
 Throws<InvalidOperationException>(()=>o.AddLine(new OrderLine("x",1,new Money(1,"usd"))));Check(o.Lines.Count==1,"currency rejection unchanged");
 o.Place();Throws<InvalidOperationException>(()=>o.AddLine(new OrderLine("x",1,Money.Vnd(1))));Check(o.Total.Amount==6,"placed unchanged");
 Throws<ArgumentOutOfRangeException>(()=>new OrderLine("x",0,Money.Vnd(1)));Throws<ArgumentOutOfRangeException>(()=>Money.Vnd(-1));
 Check(Money.Vnd(1)==new Money(1," vnd "),"value normalization");Check(!new Customer("A","N").Equals(new Customer("A","N")),"entity class reference equality");
 c.Rename("New");Check(o.CustomerId=="A","identity retained");

 }

}
