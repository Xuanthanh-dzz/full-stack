
internal static class Contracts
{
 static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
 public static void Main(){
var a=new InventoryItem("A",5m){Sku=" a "};a.Restock(3);a.Sell(2);Check(a.Stock==1 && a.Sku=="A" && a.InventoryValue==5m,"valid stock");
Throws<InvalidOperationException>(()=>a.Sell(2));Throws<ArgumentOutOfRangeException>(()=>a.ChangePrice(-1));Check(a.Stock==1&&a.Price==5m,"invalid mutation");
a.Restock(int.MaxValue-1);Throws<OverflowException>(()=>a.Restock(1));Check(a.Stock==int.MaxValue,"overflow stock");
 }
}
