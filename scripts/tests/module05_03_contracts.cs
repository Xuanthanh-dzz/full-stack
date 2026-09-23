using EventDemo;
internal static class Contracts
{
static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
static void Throws<T>(Action action) where T:Exception{try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception{try{await action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
public static void Main(){
var item=new InventoryItem("A",10,3);int calls=0;EventHandler<StockLowEventArgs> h=(sender,e)=>{Check(ReferenceEquals(sender,item)&&e.CurrentStock==3,"event snapshot");calls++;};
item.StockLow+=h;item.StockLow+=h;item.Sell(7);Check(calls==2,"duplicate handlers");item.StockLow-=h;item.Restock(7);item.Sell(7);Check(calls==3,"unsubscribe one entry");
item.StockLow-=h;item.Restock(7);bool tail=false;item.StockLow+=(_,_)=>throw new InvalidOperationException();item.StockLow+=(_,_)=>tail=true;
Throws<InvalidOperationException>(()=>item.Sell(7));Check(item.Stock==3&&!tail,"commit precedes handler failure");
}
}
