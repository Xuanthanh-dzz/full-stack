using ExceptionDemo;
internal static class Contracts
{
 static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
 public static void Main(){
var stock=new Inventory(10);var service=new OrderService(stock,new OrderRepository("missing/orders.log"));
try{service.PlaceOrder("C",2);throw new Exception("expected persistence failure");}catch(OrderPersistenceException e){Check(e.InnerException is IOException,"cause preserved");}
Check(stock.Available==10,"compensation");Throws<InventoryUnavailableException>(()=>service.PlaceOrder("C",11));Check(stock.Available==10,"insufficient stock");
Throws<ArgumentException>(()=>service.PlaceOrder("",1));Check(stock.Available==10,"invalid customer");
 }
}
